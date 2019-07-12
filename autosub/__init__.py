#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's main functionality.
"""

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

from autosub import constants
from autosub import formatters
from autosub import metadata

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
                 rate=44100, retries=3, api_key=constants.GOOGLE_SPEECH_API_KEY):
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
        print("The given file does not exist: {}.".format(filename))
        raise Exception("Invalid filepath: {}.".format(filename))
    if not ffmpeg_check():
        print("ffmpeg: Executable not found on this machine.")
        raise Exception("Dependency not found: ffmpeg.")
    command = [ffmpeg_check(), "-y", "-i", filename,
               "-ac", str(channels), "-ar", str(rate),
               "-loglevel", "error", temp.name]
    use_shell = True if os.name == "nt" else False
    subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
    return temp.name, rate


def find_speech_regions(# pylint: disable=too-many-locals
        filename, frame_width=4096,
        min_region_size=constants.MIN_REGION_SIZE,
        max_region_size=constants.MAX_REGION_SIZE):
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
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT,
        api_url_scheme=constants.DEFAULT_API_URL_SCHEME,
        api_key=None,
        min_region_size=constants.MIN_REGION_SIZE,
        max_region_size=constants.MAX_REGION_SIZE,
        ext_regions=None,
        ext_max_size_ms=constants.MAX_EXT_REGION_SIZE * 1000
    ):
    """
    Given an input audio/video file, generate subtitles in the specified language and format.
    """
    audio_filename, audio_rate = extract_audio(source_path)

    if not ext_regions:
        regions = find_speech_regions(audio_filename,
                                      min_region_size=min_region_size,
                                      max_region_size=max_region_size)
    else:
        regions = []
        for event in ext_regions.events:
            if not event.is_comment:
                # not a comment region
                reader = wave.open(audio_filename)
                audio_file_length = float(reader.getnframes()) / float(reader.getframerate())
                reader.close()
                if event.duration <= ext_max_size_ms:
                    regions.append((float(event.start) / 1000.0,
                                    float(event.start + event.duration) / 1000.0))
                else:
                    # split too long regions
                    elapsed_time = event.duration
                    start_time = event.start
                    if float(elapsed_time) / 1000.0 > audio_file_length:
                        elapsed_time = math.floor(audio_file_length) * 1000
                    while elapsed_time > ext_max_size_ms:
                        regions.append((float(start_time) / 1000.0,
                                        float(start_time + ext_max_size_ms) / 1000.0))
                        elapsed_time = elapsed_time - ext_max_size_ms
                        start_time = start_time + ext_max_size_ms
                    regions.append((float(start_time) / 1000.0,
                                    float(start_time + elapsed_time) / 1000.0))

    pool = multiprocessing.Pool(concurrency)
    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=src_language, rate=audio_rate,
                                  api_url=api_url_scheme + constants.GOOGLE_SPEECH_API_URL,
                                  api_key=constants.GOOGLE_SPEECH_API_KEY)

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
            print("Cancelling transcription.")
            return 1

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = formatters.FORMATTERS.get(subtitles_file_format)
    if formatter:
        formatted_subtitles = formatter(timed_subtitles)
    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
Using \"{default_fmt} instead.\"".format(fmt=subtitles_file_format,
                                         default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatter = formatters.FORMATTERS.get(constants.DEFAULT_SUBTITLES_FORMAT)
        formatted_subtitles = formatter(timed_subtitles)

    try:
        input_m = raw_input
    except NameError:
        input_m = input

    dest = output

    if not dest:
        base = os.path.splitext(source_path)[0]
        dest = "{base}.{langcode}.{extension}".format(base=base,
                                                      langcode=dst_language,
                                                      extension=subtitles_file_format)

    while os.path.isfile(dest):
        print("There is already a file with the same name"
              " in this location: \"{dest_name}\".".format(dest_name=dest))
        dest = input_m("Input a new path (including directory and file name) for output file.\n")
        dest = os.path.splitext(dest)[0]
        dest = "{base}.{extension}".format(base=dest,
                                           extension=subtitles_file_format)

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

    if args.format not in formatters.FORMATTERS:
        print(
            "Subtitle format not supported. "
            "Run with --list-formats to see all supported formats."
        )
        return False

    if args.src_language not in constants.SPEECH_TO_TEXT_LANGUAGE_CODES.keys():
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

    elif args.dst_language not in constants.TRANSLATION_LANGUAGE_CODES.keys():
        print(
            "Destination language not supported. "
            "Run with -ltc or --list-translation-codes "
            "to see all supported languages."
        )
        return False

    if args.min_region_size < constants.MIN_REGION_SIZE:
        print(
            "Your minimum region size {mrs0} is smaller than {mrs}.\n"
            "Now reset to {mrs}".format(mrs0=args.min_region_size,
                                        mrs=constants.MIN_REGION_SIZE)
        )
        args.min_region_size = constants.MIN_REGION_SIZE

    if args.max_region_size > constants.MAX_EXT_REGION_SIZE:
        print(
            "Your maximum region size {mrs0} is larger than {mrs}.\n"
            "Now reset to {mrs}".format(mrs0=args.max_region_size,
                                        mrs=constants.MAX_EXT_REGION_SIZE)
        )
        args.max_region_size = constants.MAX_EXT_REGION_SIZE

    return True


def main():  # pylint: disable=too-many-branches
    """
    Run autosub as a command-line program.
    """
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(
        prog=metadata.NAME,
        usage='\n  %(prog)s [options] <source_path>',
        description=metadata.DESCRIPTION,
        add_help=False
    )

    pgroup = parser.add_argument_group('Required')
    ogroup = parser.add_argument_group('Options')

    pgroup.add_argument(
        'source_path',
        nargs='?', metavar='path',
        help="The path to the video or audio file needs to generate subtitle."
    )

    ogroup.add_argument(
        '-o', '--output',
        metavar='path',
        help="""The output path for subtitle file.
                The default is in the same directory
                and the name is the source path 
                combined with the destination language code."""
    )

    ogroup.add_argument(
        '-esr', '--external-speech-regions',
        nargs='?', metavar='path',
        help="""Path to the external speech regions,
                which is one of the formats that pysubs2 supports 
                and overrides the default method to find speech regions."""
    )

    ogroup.add_argument(
        '-F', '--format',
        metavar='format',
        default=constants.DEFAULT_SUBTITLES_FORMAT,
        help="Destination subtitle format (default: %(default)s)."
    )

    ogroup.add_argument(
        '-S', '--src-language',
        metavar='locale',
        default=constants.DEFAULT_SRC_LANGUAGE,
        help="Locale of language spoken in source file (default: %(default)s)."
    )

    ogroup.add_argument(
        '-D', '--dst-language',
        metavar='locale',
        help="Locale of desired language for the subtitles (default: %(default)s)."
    )

    ogroup.add_argument(
        '-K', '--api-key',
        metavar='key',
        help="The Google Translate API key to be used. Required for subtitles translation."
    )

    ogroup.add_argument(
        '-C', '--concurrency',
        metavar='number',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent API requests to make (default: %(default)s)."
    )

    ogroup.add_argument(
        '-mnrs', '--min-region-size',
        metavar='second',
        type=float,
        default=constants.MIN_REGION_SIZE,
        help="Minimum region size "
             "when not using external speech regions control(default: %(default)s)."
    )

    ogroup.add_argument(
        '-mxrs', '--max-region-size',
        metavar='second',
        type=float,
        default=constants.MAX_REGION_SIZE,
        help="Maximum region size "
             "when not using external speech regions control(default: %(default)s)."
    )

    ogroup.add_argument(
        '-htp', '--http-speech-to-text-api',
        action='store_true',
        help="Change the speech-to-text api url into the http one."
    )

    ogroup.add_argument(
        '-lf', '--list-formats',
        action='store_true',
        help="List all available subtitles formats."
    )

    ogroup.add_argument(
        '-lsc', '--list-speech-to-text-codes',
        action='store_true',
        help="""List all available source language codes,
                which mean the available speech-to-text
                language codes.
                [WARNING]: Its name format is different from 
                           the destination language codes.
                Reference: https://cloud.google.com/speech-to-text/docs/languages"""
    )

    ogroup.add_argument(
        '-ltc', '--list-translation-codes',
        action='store_true',
        help="""List all available destination language codes,
                which mean the available translation
                language codes.
                [WARNING]: Its name format is different from 
                           the destination language codes.
                Reference: https://cloud.google.com/speech-to-text/docs/languages"""
    )

    ogroup.add_argument(
        '-h', '--help',
        action='help',
        help="Show %(prog)s help message and exit."
    )

    ogroup.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s ' + metadata.VERSION
        + ' by ' + metadata.AUTHOR + ' <'
        + metadata.AUTHOR_EMAIL + '>',
        help="Show %(prog)s version and exit."
    )

    args = parser.parse_args()

    if args.list_formats:
        print("List of formats:")
        for subtitles_format in formatters.FORMATTERS:
            print("{format}".format(format=subtitles_format))
        return 0

    if args.list_speech_to_text_codes:
        print("List of all source language codes:")
        for code, language in sorted(constants.SPEECH_TO_TEXT_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if args.list_translation_codes:
        print("List of all destination language codes:")
        for code, language in sorted(constants.TRANSLATION_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if validate(args):
        if args.http_speech_to_text_api:
            api_url_scheme = "http://"
        else:
            api_url_scheme = constants.DEFAULT_API_URL_SCHEME

        try:
            if args.external_speech_regions:
                print("Using external speech regions.")
                ext_regions = pysubs2.SSAFile.load(args.external_speech_regions)
                subtitles_file_path = generate_subtitles(
                    source_path=args.source_path,
                    concurrency=args.concurrency,
                    src_language=args.src_language,
                    dst_language=args.dst_language,
                    api_url_scheme=api_url_scheme,
                    api_key=args.api_key,
                    subtitles_file_format=args.format,
                    output=args.output,
                    min_region_size=args.min_region_size,
                    max_region_size=args.max_region_size,
                    ext_regions=ext_regions
                )

            else:
                subtitles_file_path = generate_subtitles(
                    source_path=args.source_path,
                    concurrency=args.concurrency,
                    src_language=args.src_language,
                    dst_language=args.dst_language,
                    api_url_scheme=api_url_scheme,
                    api_key=args.api_key,
                    subtitles_file_format=args.format,
                    output=args.output,
                    min_region_size=args.min_region_size,
                    max_region_size=args.max_region_size
                )
            print("\nSubtitles file created at \"{}\"".format(subtitles_file_path))

        except KeyboardInterrupt:
            return 1
        except pysubs2.exceptions.Pysubs2Error:
            print("Error: pysubs2.exceptions. Check your file format.")
            return 1

    return 0
