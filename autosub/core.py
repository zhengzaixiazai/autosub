#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's main functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import os
import wave
import multiprocessing

# Import third-party modules
import progressbar
import pysubs2
import auditok

# Any changes to the path and your own modules
from autosub import speech_trans_api
from autosub import formatters
from autosub import constants
from autosub import ffmpeg_utils


def auditok_gen_speech_regions(  # pylint: disable=too-many-arguments
        source_file,
        energy_threshold=constants.DEFAULT_ENERGY_THRESHOLD,
        min_region_size=constants.MIN_REGION_SIZE,
        max_region_size=constants.MAX_REGION_SIZE,
        max_continuous_silence=constants.MAX_CONTINUOUS_SILENCE,
        mode=auditok.StreamTokenizer.STRICT_MIN_LENGTH
):
    """
    Given an input audio/video file, generate proper speech regions.
    """
    audio_wav = ffmpeg_utils.source_to_audio(source_file)

    asource = auditok.ADSFactory.ads(
        filename=audio_wav, record=True)
    validator = auditok.AudioEnergyValidator(
        sample_width=asource.get_sample_width(),
        energy_threshold=energy_threshold)
    asource.open()
    tokenizer = auditok.StreamTokenizer(
        validator=validator,
        min_length=int(min_region_size * 100),
        max_length=int(max_region_size * 100),
        max_continuous_silence=int(max_continuous_silence * 100),
        mode=mode)

    # auditok.StreamTokenizer.DROP_TRAILING_SILENCE
    tokens = tokenizer.tokenize(asource)
    regions = []
    for token in tokens:
        # get start and end times
        regions.append((token[1] * 10, token[2] * 10))
    asource.close()
    os.remove(audio_wav)
    # reference
    # auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data
    return regions


def sub_gen_speech_regions(
        source_file,
        sub_file,
        ext_max_size_ms=constants.MAX_EXT_REGION_SIZE * 1000
):
    """
    Given an input audio/video file and subtitles file, generate proper speech regions.
    """
    regions = []
    audio_wav = ffmpeg_utils.source_to_audio(source_file)
    reader = wave.open(audio_wav)
    audio_file_length = int(float(reader.getnframes()) / float(reader.getframerate())) * 1000
    reader.close()

    ext_regions = pysubs2.SSAFile.load(sub_file)

    for event in ext_regions.events:
        if not event.is_comment:
            # not a comment region
            if event.duration <= ext_max_size_ms:
                regions.append((event.start,
                                event.start + event.duration))
            else:
                # split too long regions
                elapsed_time = event.duration
                start_time = event.start
                if elapsed_time > audio_file_length:
                    # even longer than the source file length
                    elapsed_time = audio_file_length
                while elapsed_time > ext_max_size_ms:
                    # longer than the max size limit
                    regions.append((start_time,
                                    start_time + ext_max_size_ms))
                    elapsed_time = elapsed_time - ext_max_size_ms
                    start_time = start_time + ext_max_size_ms
                regions.append((start_time,
                                start_time + elapsed_time))

    os.remove(audio_wav)
    return regions


def api_gen_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
        source_file,
        api_url,
        regions,
        api_key,
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE
):
    """
    Given an input audio/video file, generate subtitles in the specified language and format.
    """
    audio_rate = 44100
    audio_flac = ffmpeg_utils.source_to_audio(source_file, rate=audio_rate, file_ext='.flac')
    pool = multiprocessing.Pool(concurrency)
    converter = ffmpeg_utils.SplitIntoFLACPiece(source_path=audio_flac)

    recognizer = speech_trans_api.GoogleSpeechToTextV2(
        language=src_language,
        rate=audio_rate,
        api_url=api_url,
        api_key=constants.GOOGLE_SPEECH_V2_API_KEY)

    transcripts = []
    if regions:
        widgets = ["Converting speech regions to FLAC files: ",
                   progressbar.Percentage(), ' ',
                   progressbar.Bar(), ' ',
                   progressbar.ETA()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
        try:
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition: ",
                       progressbar.Percentage(), ' ',
                       progressbar.Bar(), ' ',
                       progressbar.ETA()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

            if src_language.split("-")[0] != dst_language.split("-")[0]:
                if api_key:
                    google_translate_api_key = api_key
                    translator = \
                        speech_trans_api.GoogleTranslatorV2(dst_language,
                                                            google_translate_api_key,
                                                            dst=dst_language,
                                                            src=src_language)
                    prompt = "Translating from {0} to {1}: ".format(src_language, dst_language)
                    widgets = [prompt, progressbar.Percentage(), ' ',
                               progressbar.Bar(), ' ',
                               progressbar.ETA()]
                    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
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

    os.remove(audio_flac)
    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]

    return timed_subtitles


def list_to_sub_file(  # pylint: disable=too-many-arguments
        timed_subtitles,
        output,
        fps=30.0,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT,
        input_m=input,
        ass_styles_file=None
):
    """
    Given an input timedsub list, format it and write it to file.
    """

    if subtitles_file_format == 'srt' \
            or subtitles_file_format == 'tmp':
        formatted_subtitles = formatters.pysubs2_formatter(
            subtitles=timed_subtitles,
            sub_format=subtitles_file_format)

    elif subtitles_file_format == 'ass' \
            or subtitles_file_format == 'ssa':
        if ass_styles_file:
            ass_file = pysubs2.SSAFile.load(ass_styles_file)
            ass_styles = ass_file.styles
        else:
            ass_styles = None
        formatted_subtitles = formatters.pysubs2_formatter(
            subtitles=timed_subtitles,
            sub_format=subtitles_file_format,
            ass_styles=ass_styles)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = formatters.vtt_formatter(
            subtitles=timed_subtitles)

    elif subtitles_file_format == 'json':
        formatted_subtitles = formatters.json_formatter(
            subtitles=timed_subtitles)

    elif subtitles_file_format == 'txt':
        formatted_subtitles = formatters.txt_formatter(
            subtitles=timed_subtitles)

    elif subtitles_file_format == 'sub':
        subtitles_file_format = 'microdvd'
        formatted_subtitles = formatters.pysubs2_formatter(
            subtitles=timed_subtitles,
            sub_format=subtitles_file_format,
            fps=fps)
        # sub format need fps
        # ref https://pysubs2.readthedocs.io/en/latest
        # /api-reference.html#supported-input-output-formats
        subtitles_file_format = 'sub'

    elif subtitles_file_format == 'mpl2':
        formatted_subtitles = formatters.pysubs2_formatter(
            subtitles=timed_subtitles,
            sub_format=subtitles_file_format)
        subtitles_file_format = 'mpl2.txt'

    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
        Using \"{default_fmt}\" instead.".format(fmt=subtitles_file_format,
                                                 default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatted_subtitles = formatters.pysubs2_formatter(
            subtitles=timed_subtitles,
            sub_format=constants.DEFAULT_SUBTITLES_FORMAT)

    dest = output

    while input_m and os.path.isfile(dest):
        print("There is already a file with the same name"
              " in this location: \"{dest_name}\".".format(dest_name=dest))
        dest = input_m("Input a new path (including directory and file name) for output file.\n")
        dest = os.path.splitext(dest)[0]
        dest = "{base}.{extension}".format(base=dest,
                                           extension=subtitles_file_format)

    with open(dest, 'wb') as output_file:
        output_file.write(formatted_subtitles.encode("utf-8"))

    return dest
