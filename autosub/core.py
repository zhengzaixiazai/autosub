#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's core functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import os
import multiprocessing
import time

# Import third-party modules
import progressbar
import pysubs2
import auditok
import googletrans
import langcodes

# Any changes to the path and your own modules
from autosub import speech_trans_api
from autosub import sub_utils
from autosub import constants
from autosub import ffmpeg_utils


class PrintAndStopException(Exception):
    """
    Raised when something need to print
    and works need to be stopped in main().
    """

    def __init__(self, msg):
        super(PrintAndStopException, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


def auditok_gen_speech_regions(  # pylint: disable=too-many-arguments
        source_file,
        ffmpeg_cmd="ffmpeg",
        energy_threshold=constants.DEFAULT_ENERGY_THRESHOLD,
        min_region_size=constants.MIN_REGION_SIZE,
        max_region_size=constants.MAX_REGION_SIZE,
        max_continuous_silence=constants.DEFAULT_CONTINUOUS_SILENCE,
        mode=auditok.StreamTokenizer.STRICT_MIN_LENGTH
):
    """
    Given an input audio/video file, generate proper speech regions.
    """
    audio_wav = ffmpeg_utils.source_to_audio(
        source_file,
        ffmpeg_cmd=ffmpeg_cmd)

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


def speech_to_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
        source_file,
        api_url,
        regions,
        ffmpeg_cmd="ffmpeg",
        api_key=None,
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        min_confidence=0.0
):
    """
    Given an input audio/video file, generate text_list from speech-to-text api.
    """

    if not regions:
        return None

    audio_rate = 44100
    audio_flac = ffmpeg_utils.source_to_audio(
        source_file,
        ffmpeg_cmd=ffmpeg_cmd,
        rate=audio_rate,
        file_ext='.flac')
    pool = multiprocessing.Pool(concurrency)
    converter = ffmpeg_utils.SplitIntoFLACPiece(
        source_path=audio_flac,
        ffmpeg_cmd=ffmpeg_cmd)

    if api_key:
        recognizer = speech_trans_api.GoogleSpeechToTextV2(
            api_url=api_url,
            api_key=api_key,
            min_confidence=min_confidence,
            lang_code=src_language,
            rate=audio_rate)
    else:
        recognizer = speech_trans_api.GoogleSpeechToTextV2(
            api_url=api_url,
            api_key=constants.GOOGLE_SPEECH_V2_API_KEY,
            min_confidence=min_confidence,
            lang_code=src_language,
            rate=audio_rate)

    text_list = []
    widgets = ["Converting speech regions to FLAC files: ",
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
    try:
        flac_regions = []
        for i, flac_region in enumerate(pool.imap(converter, regions)):
            flac_regions.append(flac_region)
            pbar.update(i)
        pbar.finish()

        widgets = ["Performing speech recognition: ",
                   progressbar.Percentage(), ' ',
                   progressbar.Bar(), ' ',
                   progressbar.ETA()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()

        for i, transcript in enumerate(pool.imap(recognizer, flac_regions)):
            text_list.append(transcript)
            pbar.update(i)
        pbar.finish()

    except KeyboardInterrupt:
        pbar.finish()
        pool.terminate()
        pool.join()
        print("Cancelling transcription.")
        return 1

    os.remove(audio_flac)
    return text_list


def list_to_gtv2(  # pylint: disable=too-many-locals,too-many-arguments
        text_list,
        api_key=None,
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE,
        lines_per_trans=constants.DEFAULT_LINES_PER_TRANS
):
    """
    Given a text list, generate translated text list from GoogleTranslatorV2 api.
    """

    if not text_list:
        return None

    pool = multiprocessing.Pool(concurrency)
    google_translate_api_key = api_key
    translator = \
        speech_trans_api.GoogleTranslatorV2(api_key=google_translate_api_key,
                                            src=src_language,
                                            dst=dst_language)

    prompt = "Translating from {0} to {1}: ".format(src_language, dst_language)

    if len(text_list) > lines_per_trans:
        trans_list =\
            [text_list[i:i + lines_per_trans] for i in range(0, len(text_list), lines_per_trans)]
    else:
        trans_list = [text_list]

    widgets = [prompt, progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(trans_list)).start()

    try:
        translated_text = []
        for i, transcript in enumerate(pool.imap(translator, trans_list)):
            if transcript:
                translated_text.append(transcript)
            else:
                translated_text.append([""] * len(trans_list[i]))
            pbar.update(i)
        pbar.finish()
    except KeyboardInterrupt:
        pbar.finish()
        pool.terminate()
        pool.join()
        print("Cancelling transcription.")
        return 1

    return translated_text


def list_to_googletrans(  # pylint: disable=too-many-locals
        text_list,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE,
        size_per_trans=constants.DEFAULT_SIZE_PER_TRANS,
        sleep_seconds=constants.DEFAULT_SLEEP_SECONDS
):
    """
    Given a text list, generate translated text list from GoogleTranslatorV2 api.
    """

    if not text_list:
        return None

    best_match_dst_lang = langcodes.best_match(
        dst_language,
        list(googletrans.constants.LANGUAGES.keys()))[0]

    best_match_src_lang = langcodes.best_match(
        src_language,
        list(googletrans.constants.LANGUAGES.keys()))[0]

    prompt = "Translating from {0} to {1}: ".format(best_match_src_lang, best_match_dst_lang)

    size = 0
    i = 0
    partial_index = []
    valid_index = []
    for text in text_list:
        if text:
            size = size + len(text)
            if size > size_per_trans:
                # use size_per_trans to split the list
                partial_index.append(i)
            valid_index.append(i)
        i = i + 1
    length = i

    if not partial_index:
        partial_index.append(length)
        # python sequence

    widgets = [prompt, progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=length).start()

    try:
        translated_text = []
        i = 0
        translator = googletrans.Translator()

        for index in partial_index:
            content_to_trans = '\n'.join(text_list[i:index])
            translation = translator.translate(text=content_to_trans,
                                               dest=best_match_dst_lang,
                                               src=best_match_src_lang)
            result_list = translation.text.split('\n')

            j = 0

            while i < index:
                if i == valid_index[j]:
                    # if text is the valid one, append it
                    translated_text.append(result_list[valid_index[j]])
                    j = j + 1
                else:
                    # else append an empty one
                    translated_text.append("")
                i = i + 1
                pbar.update(i)

            if len(partial_index) > 1:
                time.sleep(sleep_seconds)
        pbar.finish()

    except KeyboardInterrupt:
        pbar.finish()
        print("Cancelling transcription.")
        return 1

    return translated_text


def list_to_sub_str(  # pylint: disable=too-many-arguments
        timed_text,
        fps=30.0,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT
):
    """
    Given an input timed text list, format it to a string.
    """

    if subtitles_file_format == 'srt' \
            or subtitles_file_format == 'tmp':
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=subtitles_file_format)

    elif subtitles_file_format == 'ass' \
            or subtitles_file_format == 'ssa':
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=subtitles_file_format)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = sub_utils.vtt_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'json':
        formatted_subtitles = sub_utils.json_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'txt':
        formatted_subtitles = sub_utils.txt_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'sub':
        subtitles_file_format = 'microdvd'
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=subtitles_file_format,
            fps=fps)
        # sub format need fps
        # ref https://pysubs2.readthedocs.io/en/latest
        # /api-reference.html#supported-input-output-formats
        subtitles_file_format = 'sub'

    elif subtitles_file_format == 'mpl2':
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=subtitles_file_format)
        subtitles_file_format = 'mpl2.txt'

    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
        Using \"{default_fmt}\" instead.".format(fmt=subtitles_file_format,
                                                 default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=constants.DEFAULT_SUBTITLES_FORMAT)
        subtitles_file_format = constants.DEFAULT_SUBTITLES_FORMAT

    return formatted_subtitles, subtitles_file_format


def list_to_ass_str(  # pylint: disable=too-many-arguments
        timed_text,
        styles_list,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT,
        is_times=False
):
    """
    Given an input timed text list, format it to an ass string.
    """

    if subtitles_file_format == 'ass' \
            or subtitles_file_format == 'ssa':
        pysubs2_obj = pysubs2.SSAFile()
        pysubs2_obj.styles = \
            {styles_list[i]: styles_list[i+1] for i in range(0, len(styles_list), 2)}
        if isinstance(timed_text[0], tuple):
            sub_utils.pysubs2_ssa_event_add(
                ssafile=pysubs2_obj,
                timed_text=timed_text,
                style_name=styles_list[0],
                is_times=is_times)
        else:
            sub_utils.pysubs2_ssa_event_add(
                ssafile=pysubs2_obj,
                timed_text=timed_text[0],
                style_name=styles_list[0],
                is_times=is_times)
            if len(styles_list) == 1:
                sub_utils.pysubs2_ssa_event_add(
                    ssafile=pysubs2_obj,
                    timed_text=timed_text[1],
                    style_name=styles_list[0],
                    is_times=is_times)
            else:
                sub_utils.pysubs2_ssa_event_add(
                    ssafile=pysubs2_obj,
                    timed_text=timed_text[1],
                    style_name=styles_list[2],
                    is_times=is_times)

        formatted_subtitles = pysubs2_obj.to_string(format_=subtitles_file_format)
    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
        Using \"{default_fmt}\" instead.".format(fmt=subtitles_file_format,
                                                 default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatted_subtitles = sub_utils.pysubs2_formatter(
            timed_text=timed_text,
            sub_format=constants.DEFAULT_SUBTITLES_FORMAT)
        subtitles_file_format = constants.DEFAULT_SUBTITLES_FORMAT

    return formatted_subtitles, subtitles_file_format


def times_to_sub_str(  # pylint: disable=too-many-arguments
        times,
        fps=30.0,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT
):
    """
    Given an input timed text list, format it to a string.
    """

    if subtitles_file_format == 'srt' \
            or subtitles_file_format == 'tmp':
        formatted_subtitles = sub_utils.pysubs2_times_formatter(
            times=times,
            sub_format=subtitles_file_format)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = sub_utils.vtt_times_formatter(
            times=times)

    elif subtitles_file_format == 'json':
        formatted_subtitles = sub_utils.json_times_formatter(
            times=times)

    elif subtitles_file_format == 'sub':
        subtitles_file_format = 'microdvd'
        formatted_subtitles = sub_utils.pysubs2_times_formatter(
            times=times,
            sub_format=subtitles_file_format,
            fps=fps)
        # sub format need fps
        # ref https://pysubs2.readthedocs.io/en/latest
        # /api-reference.html#supported-input-output-formats
        subtitles_file_format = 'sub'

    elif subtitles_file_format == 'mpl2':
        formatted_subtitles = sub_utils.pysubs2_times_formatter(
            times=times,
            sub_format=subtitles_file_format)
        subtitles_file_format = 'mpl2.txt'

    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
        Using \"{default_fmt}\" instead.".format(fmt=subtitles_file_format,
                                                 default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatted_subtitles = sub_utils.pysubs2_times_formatter(
            times=times,
            sub_format=constants.DEFAULT_SUBTITLES_FORMAT)

    return formatted_subtitles, subtitles_file_format


def str_to_file(
        str_,
        output,
        extension,
        input_m=input,
):
    """
    Given a string and write it to file
    """
    dest = output

    while input_m and os.path.isfile(dest):
        print("There is already a file with the same name"
              " in this location: \"{dest_name}\".".format(dest_name=dest))
        dest = input_m("Input a new path (including directory and file name) for output file.\n")
        dest = os.path.splitext(dest)[0]
        dest = "{base}.{extension}".format(base=dest,
                                           extension=extension)

    with open(dest, 'wb') as output_file:
        output_file.write(str_.encode("utf-8"))

    return dest
