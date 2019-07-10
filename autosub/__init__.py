"""
Defines autosub's main functionality.
"""

#!/usr/bin/env python

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import audioop
import math
import multiprocessing
import os
import subprocess
import tempfile
import wave
import json
import requests
import pysubs2
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from googleapiclient.discovery import build
from progressbar import ProgressBar, Percentage, Bar, ETA

from autosub.constants import (
    SPEECH_TO_TEXT_LANGUAGE_CODES, TRANSLATION_LANGUAGE_CODES,
    GOOGLE_SPEECH_API_KEY, GOOGLE_SPEECH_API_URL,
)
from autosub.formatters import FORMATTERS

DEFAULT_SUBTITLE_FORMAT = 'srt'
DEFAULT_CONCURRENCY = 10
DEFAULT_SRC_LANGUAGE = 'en-US'
DEFAULT_DST_LANGUAGE = 'en-US'
DEFAULT_API_URL_SCHEME = 'https://'
MAX_EXT_REGION_LENGTH = 10000
# Maximum speech to text region length in milliseconds
# when using external speech region control

def percentile(arr, percent):
    """
    Calculate the given percentile of arr.
    """
    arr = sorted(arr)
    index = (len(arr) - 1) * percent
    floor = math.floor(index)
    ceil = math.ceil(index)
    if floor == ceil:
        return arr[int(index)]
    low_value = arr[int(floor)] * (ceil - index)
    high_value = arr[int(ceil)] * (index - floor)
    return low_value + high_value


class FLACConverter(object): # pylint: disable=too-few-public-methods
    """
    Class for converting a region of an input audio or video file into a FLAC audio file
    """
    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            start, end = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            command = ["ffmpeg", "-ss", str(start), "-t", str(end - start),
                       "-y", "-i", self.source_path,
                       "-loglevel", "error", temp.name]
            use_shell = True if os.name == "nt" else False
            subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
            read_data = temp.read()
            temp.close()
            os.unlink(temp.name)
            return read_data

        except KeyboardInterrupt:
            return None


class SpeechRecognizer(object): # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text for an input FLAC file.
    """
    def __init__(self, api_url, language="en",
                 rate=44100, retries=3, api_key=GOOGLE_SPEECH_API_KEY):
                 # pylint: disable=too-many-arguments
        self.language = language
        self.rate = rate
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for _ in range(self.retries):
                url = self.api_url.format(lang=self.language, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line = line['result'][0]['alternative'][0]['transcript']
                        return line[:1].upper() + line[1:]
                    except (JSONDecodeError, ValueError, IndexError):
                        # no result
                        continue

        except KeyboardInterrupt:
            return None


class Translator(object):  # pylint: disable=too-few-public-methods
    """
    Class for translating a sentence from a one language to another.
    """
    def __init__(self, language, api_key, src, dst):
        self.language = language
        self.api_key = api_key
        self.service = build('translate', 'v2',
                             developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, sentence):
        try:
            if not sentence:
                return None

            result = self.service.translations().list( # pylint: disable=no-member
                source=self.src,
                target=self.dst,
                q=[sentence]
            ).execute()

            if 'translations' in result and result['translations'] and \
                'translatedText' in result['translations'][0]:
                return result['translations'][0]['translatedText']

            return None

        except KeyboardInterrupt:
            return None


def which(program):
    """
    Return the path for a given executable.
    """
    def is_exe(file_path):
        """
        Checks whether a file is executable.
        """
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def ffmpeg_check():
    """
    Return the ffmpeg executable name. "None" returned when no executable exists.
    """
    if which("ffmpeg"):
        return "ffmpeg"
    if which("ffmpeg.exe"):
        return "ffmpeg.exe"
    return None


def extract_audio(filename, channels=1, rate=16000):
    """
    Extract audio from an input file to a temporary WAV file.
    """
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    if not os.path.isfile(filename):
        print("The given file does not exist: {}".format(filename))
        raise Exception("Invalid filepath: {}".format(filename))
    if not ffmpeg_check():
        print("ffmpeg: Executable not found on machine.")
        raise Exception("Dependency not found: ffmpeg")
    command = [ffmpeg_check(), "-y", "-i", filename,
               "-ac", str(channels), "-ar", str(rate),
               "-loglevel", "error", temp.name]
    use_shell = True if os.name == "nt" else False
    subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
    return temp.name, rate


def find_speech_regions(filename, frame_width=4096, min_region_size=0.5, max_region_size=6): # pylint: disable=too-many-locals
    """
    Perform voice activity detection on a given audio file.
    """
    reader = wave.open(filename)
    sample_width = reader.getsampwidth()
    rate = reader.getframerate()
    n_channels = reader.getnchannels()
    chunk_duration = float(frame_width) / rate

    n_chunks = int(math.ceil(reader.getnframes()*1.0 / frame_width))
    energies = []

    for _ in range(n_chunks):
        chunk = reader.readframes(frame_width)
        energies.append(audioop.rms(chunk, sample_width * n_channels))

    threshold = percentile(energies, 0.2)

    region_end = 0

    regions = []
    region_start = None

    for energy in energies:
        is_silence = energy <= threshold
        max_exceeded = region_start and region_end - region_start >= max_region_size

        if (max_exceeded or is_silence) and region_start:
            if region_end - region_start >= min_region_size:
                regions.append((region_start, region_end))
                region_start = None

        elif (not region_start) and (not is_silence):
            region_start = region_end
        region_end += chunk_duration
    return regions


def generate_subtitles( # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
        source_path,
        output=None,
        concurrency=DEFAULT_CONCURRENCY,
        src_language=DEFAULT_SRC_LANGUAGE,
        dst_language=DEFAULT_DST_LANGUAGE,
        subtitle_file_format=DEFAULT_SUBTITLE_FORMAT,
        api_url_scheme=DEFAULT_API_URL_SCHEME,
        api_key=None,
        ext_regions=None,
        ext_max_length=MAX_EXT_REGION_LENGTH
    ):
    """
    Given an input audio/video file, generate subtitles in the specified language and format.
    """
    audio_filename, audio_rate = extract_audio(source_path)

    if not ext_regions:
        regions = find_speech_regions(audio_filename)
    else:
        regions = []
        for event in ext_regions.events:
            if not event.is_comment:
                # not a comment region
                reader = wave.open(audio_filename)
                audio_file_length = float(reader.getnframes()) / float(reader.getframerate())
                reader.close()
                if event.duration <= ext_max_length:
                    regions.append((float(event.start) / 1000.0,
                                    float(event.start + event.duration) / 1000.0))
                else:
                    # split too long regions
                    elapsed_time = event.duration
                    start_time = event.start
                    if float(elapsed_time) / 1000.0 > audio_file_length:
                        elapsed_time = math.floor(audio_file_length) * 1000
                    while elapsed_time > ext_max_length:
                        regions.append((float(start_time) / 1000.0,
                                        float(start_time + ext_max_length) / 1000.0))
                        elapsed_time = elapsed_time - ext_max_length
                        start_time = start_time + ext_max_length
                    regions.append((float(start_time) / 1000.0,
                                    float(start_time + elapsed_time) / 1000.0))

    pool = multiprocessing.Pool(concurrency)
    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=src_language, rate=audio_rate,
                                  api_url=api_url_scheme + GOOGLE_SPEECH_API_URL,
                                  api_key=GOOGLE_SPEECH_API_KEY)

    transcripts = []
    if regions:
        widgets = ["Converting speech regions to FLAC files: ", Percentage(), ' ', Bar(), ' ',
                   ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
        try:
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

            if src_language.split("-")[0] != dst_language.split("-")[0]:
                if api_key:
                    google_translate_api_key = api_key
                    translator = Translator(dst_language, google_translate_api_key,
                                            dst=dst_language,
                                            src=src_language)
                    prompt = "Translating from {0} to {1}: ".format(src_language, dst_language)
                    widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
                    pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
                    translated_transcripts = []
                    for i, transcript in enumerate(pool.imap(translator, transcripts)):
                        translated_transcripts.append(transcript)
                        pbar.update(i)
                    pbar.finish()
                    transcripts = translated_transcripts
                else:
                    print(
                        "Error: Subtitle translation requires specified Google Translate API key. "
                        "See --help for further information."
                    )
                    return 1

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.join()
            print("Cancelling transcription")
            raise

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(subtitle_file_format)
    formatted_subtitles = formatter(timed_subtitles)

    dest = output

    if not dest:
        base = os.path.splitext(source_path)[0]
        dest = "{base}.{format}".format(base=base, format=subtitle_file_format)

    with open(dest, 'wb') as output_file:
        output_file.write(formatted_subtitles.encode("utf-8"))

    os.remove(audio_filename)

    return dest


def validate(args):
    """
    Check that the CLI arguments passed to autosub are valid.
    """
    if not args.source_path:
        print("Error: You need to specify a source path.")
        return False

    if args.format not in FORMATTERS:
        print(
            "Subtitle format not supported. "
            "Run with --list-formats to see all supported formats."
        )
        return False

    if args.src_language not in SPEECH_TO_TEXT_LANGUAGE_CODES.keys():
        print(
            "Source language not supported. "
            "Run with -lsc or --list-speech-to-text-codes "
            "to see all supported languages."
        )
        return False

    if args.dst_language is None:
        print(
            "Destination language not provided. "
            "Only performing speech recognition."
        )
        args.dst_language = args.src_language

    elif args.dst_language == args.src_language:
        print(
            "Source language is the same as the Destination language. "
            "Only performing speech recognition."
        )

    elif args.dst_language not in TRANSLATION_LANGUAGE_CODES.keys():
        print(
            "Destination language not supported. "
            "Run with -ltc or --list-translation-codes "
            "to see all supported languages."
        )
        return False

    return True


def main():  # pylint: disable=too-many-branches
    """
    Run autosub as a command-line program.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle",
                        nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make",
                        type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument('-o', '--output',
                        help="Output path for subtitles (by default, subtitles are saved in \
                        the same directory and name as the source path)")
    parser.add_argument('-esr', '--external-speech-regions',
                        help="Path to the external speech regions, \
                        which is one of the formats that pysubs2 supports \
                        and overrides the default method to find speech regions",
                        nargs="?", metavar="path")
    parser.add_argument('-F', '--format', help="Destination subtitle format",
                        default=DEFAULT_SUBTITLE_FORMAT)
    parser.add_argument('-S', '--src-language', help="Language spoken in source file",
                        default=DEFAULT_SRC_LANGUAGE)
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles")
    parser.add_argument('-K', '--api-key',
                        help="The Google Translation API key to be used. \
                        (Required for subtitle translation)")
    parser.add_argument('-lf', '--list-formats', help="List all available subtitle formats",
                        action='store_true')
    parser.add_argument('-lsc', '--list-speech-to-text-codes',
                        help="""List all available source language codes,
                              which mean the speech-to-text
                              available language codes.
                              [WARNING]: Its name format is different from 
                                         the destination language codes.
                                         And it's Google who make that difference
                                         not the developers of the autosub.
                              Reference: https://cloud.google.com/speech-to-text/docs/languages""",
                        action='store_true')
    parser.add_argument('-ltc', '--list-translation-codes',
                        help="""List all available destination language codes,
                             which mean the translation
                             language codes.
                             [WARNING]: Its name format is different from 
                                        the source language codes.
                                        And it's Google who make that difference
                                        not the developers of the autosub.
                             Reference: https://cloud.google.com/translate/docs/languages""",
                        action='store_true')
    parser.add_argument('-htp', '--http-speech-to-text-api',
                        help="Change the speech-to-text api url into the http one",
                        action='store_true')

    args = parser.parse_args()

    if args.list_formats:
        print("List of formats:")
        for subtitle_format in FORMATTERS:
            print("{format}".format(format=subtitle_format))
        return 0

    if args.list_speech_to_text_codes:
        print("List of all source language codes:")
        for code, language in sorted(SPEECH_TO_TEXT_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if args.list_translation_codes:
        print("List of all destination language codes:")
        for code, language in sorted(TRANSLATION_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if validate(args):
        if args.http_speech_to_text_api:
            api_url_scheme = "http://"
        else:
            api_url_scheme = DEFAULT_API_URL_SCHEME

        try:
            if args.external_speech_regions:
                print("Using external speech regions.")
                ext_regions = pysubs2.SSAFile.load(args.external_speech_regions)
                subtitle_file_path = generate_subtitles(
                    source_path=args.source_path,
                    concurrency=args.concurrency,
                    src_language=args.src_language,
                    dst_language=args.dst_language,
                    api_url_scheme=api_url_scheme,
                    api_key=args.api_key,
                    subtitle_file_format=args.format,
                    output=args.output,
                    ext_regions=ext_regions
                )

            else:
                subtitle_file_path = generate_subtitles(
                    source_path=args.source_path,
                    concurrency=args.concurrency,
                    src_language=args.src_language,
                    dst_language=args.dst_language,
                    api_url_scheme=api_url_scheme,
                    api_key=args.api_key,
                    subtitle_file_format=args.format,
                    output=args.output
                )
            print("Subtitles file created at {}".format(subtitle_file_path))

        except KeyboardInterrupt:
            return 1
        except pysubs2.exceptions.Pysubs2Error:
            print("Error: pysubs2.exceptions. Check your file format.")
            return 1

    return 0
