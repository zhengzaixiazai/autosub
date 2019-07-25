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
import gettext

# Import third-party modules
import progressbar
import pysubs2
import auditok
import googletrans

# Any changes to the path and your own modules
from autosub import speech_trans_api
from autosub import sub_utils
from autosub import constants
from autosub import ffmpeg_utils

CORE_TEXT = gettext.translation(domain=__name__,
                                localedir=constants.LOCALE_PATH,
                                languages=[constants.CURRENT_LOCALE],
                                fallback=True)

try:
    _ = CORE_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = CORE_TEXT.gettext


def auditok_gen_speech_regions(  # pylint: disable=too-many-arguments
        audio_wav,
        energy_threshold=constants.DEFAULT_ENERGY_THRESHOLD,
        min_region_size=constants.MIN_REGION_SIZE,
        max_region_size=constants.MAX_REGION_SIZE,
        max_continuous_silence=constants.DEFAULT_CONTINUOUS_SILENCE,
        mode=auditok.StreamTokenizer.STRICT_MIN_LENGTH
):
    """
    Give an input audio/video file, generate proper speech regions.
    """
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
    # reference
    # auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data
    return regions


def bulk_audio_conversion(  # pylint: disable=too-many-arguments
        source_file,
        regions,
        split_cmd,
        suffix,
        concurrency=constants.DEFAULT_CONCURRENCY,
        output=None,
        is_keep=False
):
    """
    Give an input audio/video file and
    generate short-term audio fragments.
    """

    if not regions:
        return None

    pool = multiprocessing.Pool(concurrency)

    converter = ffmpeg_utils.SplitIntoAudioPiece(
        source_path=source_file,
        cmd=split_cmd,
        suffix=suffix,
        output=output,
        is_keep=is_keep)

    print("\nConverting speech regions to short-term fragments.")
    widgets = ["Converting: ",
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
    try:
        audio_fragments = []
        for i, flac_region in enumerate(pool.imap(converter, regions)):
            audio_fragments.append(flac_region)
            pbar.update(i)
        pbar.finish()

    except KeyboardInterrupt:
        pbar.finish()
        pool.terminate()
        pool.join()
        return None

    return audio_fragments


def audio_to_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
        audio_fragments,
        api_url,
        regions,
        api_key=None,
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        min_confidence=0.0,
        audio_rate=44100,
        is_keep=False
):
    """
    Give a list of short-term audio fragment files
    and generate text_list from speech-to-text api.
    """
    if not regions:
        return None

    text_list = []
    pool = multiprocessing.Pool(concurrency)
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
            rate=audio_rate,
            is_keep=is_keep)

    print("\nSending short-term fragments to API and getting result.")
    widgets = ["Speech-to-Text: ",
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
    try:
        for i, transcript in enumerate(pool.imap(recognizer, audio_fragments)):
            if transcript:
                text_list.append(transcript)
                pbar.update(i)
            else:
                text_list.append("")
        pbar.finish()

    except KeyboardInterrupt:
        pbar.finish()
        pool.terminate()
        pool.join()
        return None

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
    Give a text list, generate translated text list from GoogleTranslatorV2 api.
    """

    if not text_list:
        return None

    pool = multiprocessing.Pool(concurrency)
    google_translate_api_key = api_key
    translator = \
        speech_trans_api.GoogleTranslatorV2(api_key=google_translate_api_key,
                                            src=src_language,
                                            dst=dst_language)

    print("\nTranslating text from {0} to {1}.".format(
        src_language,
        dst_language))

    if len(text_list) > lines_per_trans:
        trans_list =\
            [text_list[i:i + lines_per_trans] for i in range(0, len(text_list), lines_per_trans)]
    else:
        trans_list = [text_list]

    widgets = ["Translation: ",
               progressbar.Percentage(), ' ',
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


def list_to_googletrans(  # pylint: disable=too-many-locals, too-many-arguments
        text_list,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE,
        size_per_trans=constants.DEFAULT_SIZE_PER_TRANS,
        sleep_seconds=constants.DEFAULT_SLEEP_SECONDS,
        user_agent=None,
        service_urls=None
):
    """
    Give a text list, generate translated text list from GoogleTranslatorV2 api.
    """

    if not text_list:
        return None

    print("\nTranslating text from {0} to {1}.".format(
        src_language,
        dst_language))

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
                size = 0
            valid_index.append(i)
            # valid_index for valid text position
        i = i + 1
    if size:
        partial_index.append(i)
        # python sequence
        # every group's end index

    widgets = ["Translation: ",
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=i).start()

    try:
        translated_text = []
        i = 0
        # total position
        j = 0
        # valid_index position
        last_index = 0
        translator = googletrans.Translator(
            user_agent=user_agent,
            service_urls=service_urls)

        for index in partial_index:
            content_to_trans = '\n'.join(text_list[i:index])
            translation = translator.translate(text=content_to_trans,
                                               dest=dst_language,
                                               src=src_language)
            result_text = translation.text.replace('’', '\'')
            result_list = result_text.split('\n')

            while i < index:
                if i == valid_index[j]:
                    # if text is the valid one, append it
                    translated_text.append(
                        result_list[valid_index[j] - last_index])
                    # minus last group's length
                    j = j + 1
                else:
                    # else append an empty one
                    translated_text.append("")

                i = i + 1
                pbar.update(i)

            last_index = index

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
    Give an input timed text list, format it to a string.
    """

    if subtitles_file_format == 'srt' \
            or subtitles_file_format == 'tmp'\
            or subtitles_file_format == 'ass'\
            or subtitles_file_format == 'ssa':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_=subtitles_file_format)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = sub_utils.vtt_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'json':
        formatted_subtitles = sub_utils.json_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'ass.json':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_='json')

    elif subtitles_file_format == 'txt':
        formatted_subtitles = sub_utils.txt_formatter(
            subtitles=timed_text)

    elif subtitles_file_format == 'sub':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_='microdvd',
            fps=fps)
        # sub format need fps
        # ref https://pysubs2.readthedocs.io/en/latest
        # /api-reference.html#supported-input-output-formats

    elif subtitles_file_format == 'mpl2.txt':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_='mpl2',
            fps=fps)

    else:
        # fallback process
        print("Format \"{fmt}\" not supported. \
        Using \"{default_fmt}\" instead.".format(
            fmt=subtitles_file_format,
            default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_=constants.DEFAULT_SUBTITLES_FORMAT)

    return formatted_subtitles


def list_to_ass_str(  # pylint: disable=too-many-arguments
        text_list,
        styles_list,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT
):
    """
    Give an input timed text list, format it to an ass string.
    """

    if subtitles_file_format == 'ass' \
            or subtitles_file_format == 'ssa'\
            or subtitles_file_format == 'ass.json':
        pysubs2_obj = pysubs2.SSAFile()
        pysubs2_obj.styles = \
            {styles_list[i]: styles_list[i + 1] for i in range(0, len(styles_list), 2)}
        if not isinstance(text_list[0], list):
            # text_list is [((start, end), text), ...]
            # text_list provides regions
            sub_utils.pysubs2_ssa_event_add(
                src_ssafile=None,
                dst_ssafile=pysubs2_obj,
                text_list=text_list,
                style_name=styles_list[0])
        else:
            # text_list is [[src_list], [dst_list]]
            # src_list provides regions
            sub_utils.pysubs2_ssa_event_add(
                src_ssafile=None,
                dst_ssafile=pysubs2_obj,
                text_list=text_list[0],
                style_name=styles_list[0])
            if len(styles_list) == 1:
                sub_utils.pysubs2_ssa_event_add(
                    src_ssafile=None,
                    dst_ssafile=pysubs2_obj,
                    text_list=text_list[1],
                    style_name=styles_list[0])
            else:
                sub_utils.pysubs2_ssa_event_add(
                    src_ssafile=None,
                    dst_ssafile=pysubs2_obj,
                    text_list=text_list[1],
                    style_name=styles_list[2])

        if subtitles_file_format != 'ass.json':
            formatted_subtitles = pysubs2_obj.to_string(format_=subtitles_file_format)
        else:
            formatted_subtitles = pysubs2_obj.to_string(format_='json')
    else:
        # fallback process
        print("Format \"{fmt}\" not supported. "
              "Using \"{default_fmt}\" instead.".format(
                  fmt=subtitles_file_format,
                  default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=text_list,
            style_name=None
        )
        formatted_subtitles = pysubs2_obj.to_string(
            format_=constants.DEFAULT_SUBTITLES_FORMAT)

    return formatted_subtitles, subtitles_file_format


def str_to_file(
        str_,
        output,
        input_m=input
):
    """
    Give a string and write it to file
    """
    dest = output

    if input_m:
        while os.path.isfile(dest):
            print("There is already a file with the same name "
                  "in this location: \"{dest_name}\".".format(dest_name=dest))
            dest = input_m(
                "Input a new path (including directory and file name) for output file.\n")
            dest = os.path.splitext(dest)[0]
            dest = "{base}".format(base=dest)

    with open(dest, 'wb') as output_file:
        output_file.write(str_.encode("utf-8"))

    return dest
