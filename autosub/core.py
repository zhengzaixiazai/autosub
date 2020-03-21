#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines autosub's core functionality.
"""
# Import built-in modules
import os
import multiprocessing
import time
import gettext
import gc
import re

# Import third-party modules
import progressbar
import pysubs2
import auditok
import googletrans
import wcwidth

# Any changes to the path and your own modules
from autosub import google_api
from autosub import xfyun_api
from autosub import sub_utils
from autosub import constants
from autosub import ffmpeg_utils
from autosub import exceptions

if constants.IS_GOOGLECLOUDCLIENT:
    from google.cloud.speech_v1p1beta1 import enums
else:
    enums = None  # pylint: disable=invalid-name

CORE_TEXT = gettext.translation(domain=__name__,
                                localedir=constants.LOCALE_PATH,
                                languages=[constants.CURRENT_LOCALE],
                                fallback=True)

_ = CORE_TEXT.gettext


def extension_to_encoding(
        extension,
        is_string=True):
    """
    File extension to audio encoding.
    """
    ext = extension.lower()
    if is_string:
        if ext.endswith(".flac"):
            encoding = "FLAC"
        elif ext.endswith(".mp3"):
            encoding = "MP3"
        elif ext.endswith(".wav")\
                or ext.endswith(".pcm"):
            # regard WAV as PCM
            encoding = "LINEAR16"
        elif ext.endswith(".ogg"):
            encoding = "OGG_OPUS"
        else:
            encoding = ""

    else:
        # https://cloud.google.com/speech-to-text/docs/reference/rest/v1p1beta1/RecognitionConfig?hl=zh-cn#AudioEncoding
        if ext.endswith(".flac"):
            encoding = \
                enums.RecognitionConfig.AudioEncoding.FLAC
            # encoding = 2
        elif ext.endswith(".mp3"):
            encoding = \
                enums.RecognitionConfig.AudioEncoding.MP3
            # encoding = 8
        elif ext.endswith(".wav")\
                or extension.lower().endswith(".pcm"):
            # regard WAV as PCM
            encoding = \
                enums.RecognitionConfig.AudioEncoding.LINEAR16
            # encoding = 1
        elif ext.endswith(".ogg"):
            encoding = \
                enums.RecognitionConfig.AudioEncoding.OGG_OPUS
            # encoding = 6
        else:
            encoding = \
                enums.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
            # encoding = 0

    return encoding


def encoding_to_extension(  # pylint: disable=too-many-branches
        encoding):
    """
    Audio encoding to file extension.
    """
    if isinstance(encoding, str):
        if encoding == "FLAC":
            extension = ".flac"
        elif encoding == "MP3":
            extension = ".mp3"
        elif encoding == "LINEAR16":
            extension = ".wav"
        elif encoding == "OGG_OPUS":
            extension = ".ogg"
        else:
            extension = ".flac"

    elif isinstance(encoding, int):
        # https://cloud.google.com/speech-to-text/docs/reference/rest/v1p1beta1/RecognitionConfig?hl=zh-cn#AudioEncoding
        if encoding == 2:
            extension = ".flac"
        elif encoding == 8:
            extension = ".mp3"
        elif encoding == 1:
            extension = ".wav"
        elif encoding == 6:
            extension = ".ogg"
        else:
            extension = ".flac"

    else:
        extension = ".flac"

    return extension


def auditok_gen_speech_regions(  # pylint: disable=too-many-arguments
        audio_wav,
        energy_threshold=constants.DEFAULT_ENERGY_THRESHOLD,
        min_region_size=constants.DEFAULT_MIN_REGION_SIZE,
        max_region_size=constants.DEFAULT_MAX_REGION_SIZE,
        max_continuous_silence=constants.DEFAULT_CONTINUOUS_SILENCE,
        mode=auditok.StreamTokenizer.STRICT_MIN_LENGTH):
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
        is_keep=False):
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

    print(_("\nConverting speech regions to short-term fragments."))
    widgets = [_("Converting: "),
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(regions)).start()
    try:
        audio_fragments = []
        for i, flac_region in enumerate(pool.imap(converter, regions)):
            audio_fragments.append(flac_region)
            pbar.update(i)
            gc.collect(0)
        pbar.finish()
        pool.terminate()
        pool.join()

    except KeyboardInterrupt:
        pbar.finish()
        pool.terminate()
        pool.join()
        return None
    return audio_fragments


def gsv2_to_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
        audio_fragments,
        api_url,
        headers,
        concurrency=constants.DEFAULT_CONCURRENCY,
        min_confidence=0.0,
        is_keep=False,
        result_list=None):
    """
    Give a list of short-term audio fragment files
    and generate text_list from Google speech-to-text V2 api.
    """
    text_list = []
    pool = multiprocessing.Pool(concurrency)

    recognizer = google_api.GoogleSpeechV2(
        api_url=api_url,
        headers=headers,
        min_confidence=min_confidence,
        is_keep=is_keep,
        is_full_result=result_list is not None)

    print(_("\nSending short-term fragments to Google Speech V2 API and getting result."))
    widgets = [_("Speech-to-Text: "),
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(audio_fragments)).start()
    try:
        # get transcript
        if result_list is None:
            for i, transcript in enumerate(pool.imap(recognizer, audio_fragments)):
                if transcript:
                    text_list.append(transcript)
                else:
                    text_list.append("")
                gc.collect(0)
                pbar.update(i)
        # get full result and transcript
        else:
            for i, result in enumerate(pool.imap(recognizer, audio_fragments)):
                if result:
                    result_list.append(result)
                    transcript = \
                        google_api.get_google_speech_v2_transcript(min_confidence, result)
                    if transcript:
                        text_list.append(transcript)
                        continue
                else:
                    result_list.append("")
                text_list.append("")
                gc.collect(0)
                pbar.update(i)
        pbar.finish()
        pool.terminate()
        pool.join()

    except (KeyboardInterrupt, AttributeError) as error:
        pbar.finish()
        pool.terminate()
        pool.join()

        if error == AttributeError:
            print(
                _("Error: Connection error happened too many times.\nAll works done."))

        return None

    return text_list


def gcsv1_to_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements, too-many-nested-blocks
        audio_fragments,
        sample_rate,
        api_url=None,
        headers=None,
        config=None,
        concurrency=constants.DEFAULT_CONCURRENCY,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        min_confidence=0.0,
        is_keep=False,
        result_list=None):
    """
    Give a list of short-term audio fragment files
    and generate text_list from Google cloud speech-to-text V1P1Beta1 api.
    """

    text_list = []
    pool = multiprocessing.Pool(concurrency)

    print(_("\nSending short-term fragments to Google Cloud Speech V1P1Beta1 API"
            " and getting result."))
    widgets = [_("Speech-to-Text: "),
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(audio_fragments)).start()

    try:
        if api_url:
            # https://cloud.google.com/speech-to-text/docs/reference/rest/v1p1beta1/RecognitionConfig
            if config:
                # Use the fixed argument
                if "languageCode" in config:
                    config["languageCode"] = src_language
                else:
                    config["language_code"] = src_language
            else:
                config = {
                    "encoding": extension_to_encoding(audio_fragments[0]),
                    "sampleRateHertz": sample_rate,
                    "languageCode": src_language}

            recognizer = google_api.GCSV1P1Beta1URL(
                config=config,
                api_url=api_url,
                headers=headers,
                min_confidence=min_confidence,
                is_keep=is_keep,
                is_full_result=result_list is not None)

            # get transcript
            if result_list is None:
                for i, transcript in enumerate(pool.imap(recognizer, audio_fragments)):
                    if transcript:
                        text_list.append(transcript)
                    else:
                        text_list.append("")
                    pbar.update(i)
            # get full result and transcript
            else:
                for i, result in enumerate(pool.imap(recognizer, audio_fragments)):
                    if result:
                        result_list.append(result)
                        transcript = google_api.get_gcsv1p1beta1_transcript(
                            min_confidence,
                            result)
                        if transcript:
                            text_list.append(transcript)
                            continue
                    else:
                        result_list.append("")
                    text_list.append("")
                    pbar.update(i)

        else:
            # https://googleapis.dev/python/speech/latest/gapic/v1/types.html#google.cloud.speech_v1.types.RecognitionConfig
            if config:
                # Use the fixed arguments
                config["encoding"] = extension_to_encoding(
                    extension=audio_fragments[0],
                    is_string=False
                )
                config["language_code"] = src_language
            else:
                config = {
                    "encoding": extension_to_encoding(
                        extension=audio_fragments[0],
                        is_string=False),
                    "sample_rate_hertz": sample_rate,
                    "language_code": src_language}

            i = 0
            tasks = []
            for filename in audio_fragments:
                # google cloud speech-to-text client can't use multiprocessing.pool
                # based on class call, otherwise will receive pickling error
                tasks.append(pool.apply_async(
                    google_api.gcsv1p1beta1_service_client,
                    args=(filename, is_keep, config, min_confidence,
                          result_list is not None)))
                gc.collect(0)

            if result_list is None:
                for task in tasks:
                    i = i + 1
                    transcript = task.get()
                    if transcript:
                        text_list.append(transcript)
                    else:
                        text_list.append("")
                    pbar.update(i)
            else:
                for task in tasks:
                    i = i + 1
                    result = task.get()
                    result_list.append(result)
                    transcript = google_api.get_gcsv1p1beta1_transcript(
                        min_confidence,
                        result)
                    if transcript:
                        text_list.append(transcript)
                    else:
                        text_list.append("")
                    pbar.update(i)

        pbar.finish()
        pool.terminate()
        pool.join()

    except (KeyboardInterrupt, AttributeError) as error:
        pbar.finish()
        pool.terminate()
        pool.join()

        if error == AttributeError:
            print(
                _("Error: Connection error happened too many times.\nAll works done."))

        return None

    except exceptions.SpeechToTextException as err_msg:
        pbar.finish()
        pool.terminate()
        pool.join()
        print(_("Receive something unexpected:"))
        print(err_msg)
        return None

    return text_list


def xfyun_to_text(  # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements, too-many-nested-blocks
        audio_fragments,
        config,
        concurrency=constants.DEFAULT_CONCURRENCY,
        is_keep=False,
        result_list=None):
    """
    Give a list of short-term audio fragment files
    and generate text_list from Google cloud speech-to-text V1P1Beta1 api.
    """

    text_list = []

    if "api_address" in config:
        api_address = config["api_address"]
    else:
        api_address = constants.XFYUN_SPEECH_WEBAPI_URL

    if "delete_chars" in config:
        delete_chars = config["delete_chars"]
    else:
        delete_chars = None

    pool = multiprocessing.Pool(concurrency)

    print(_("\nSending short-term fragments to Xun Fei Yun WebSocket API"
            " and getting result."))
    widgets = [_("Speech-to-Text: "),
               progressbar.Percentage(), ' ',
               progressbar.Bar(), ' ',
               progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(audio_fragments)).start()

    try:
        recognizer = xfyun_api.XfyunWebSocketAPI(
            app_id=config["app_id"],
            api_key=config["api_key"],
            api_secret=config["api_secret"],
            api_address=api_address,
            business_args=config["business"],
            is_keep=is_keep,
            is_full_result=result_list is not None,
            delete_chars=delete_chars)

        # get transcript
        if result_list is None:
            for i, transcript in enumerate(pool.imap(recognizer, audio_fragments)):
                if transcript:
                    text_list.append(transcript)
                else:
                    text_list.append("")
                pbar.update(i)
        # get full result and transcript
        else:
            for i, result in enumerate(pool.imap(recognizer, audio_fragments)):
                if result:
                    result_list.append(result)
                    transcript = ""
                    for item in result:
                        transcript = transcript + xfyun_api.get_xfyun_transcript(item)
                    if transcript:
                        text_list.append(transcript)
                        continue
                else:
                    result_list.append("")
                text_list.append("")
                pbar.update(i)
        pbar.finish()
        pool.terminate()
        pool.join()

    except (KeyboardInterrupt, AttributeError) as error:
        pbar.finish()
        pool.terminate()
        pool.join()

        if error == AttributeError:
            print(
                _("Error: Connection error happened too many times.\nAll works done."))

        return None

    except exceptions.SpeechToTextException as err_msg:
        pbar.finish()
        pool.terminate()
        pool.join()
        print(_("Receive something unexpected:"))
        print(err_msg)
        return None

    return text_list


def list_to_googletrans(  # pylint: disable=too-many-locals, too-many-arguments, too-many-branches, too-many-statements
        text_list,
        src_language=constants.DEFAULT_SRC_LANGUAGE,
        dst_language=constants.DEFAULT_DST_LANGUAGE,
        size_per_trans=constants.DEFAULT_SIZE_PER_TRANS,
        sleep_seconds=constants.DEFAULT_SLEEP_SECONDS,
        user_agent=None,
        service_urls=None,
        drop_override_codes=False):
    """
    Give a text list, generate translated text list from GoogleTranslatorV2 api.
    """

    if not text_list:
        return None

    print(_("\nTranslating text from \"{0}\" to \"{1}\".").format(
        src_language,
        dst_language))

    size = 0
    i = 0
    partial_index = []
    valid_index = []
    is_last = ""
    for text in text_list:
        if text:
            if not is_last:
                is_last = text
                valid_index.append(i)
                # valid_index for valid text position start
            wcswidth_text = wcwidth.wcswidth(text)
            if wcswidth_text * 10 / len(text) >= 10:
                # If text contains full-wide char,
                # count its length about 4 times than the ordinary text.
                # Avoid weird problem when text has full-wide char.
                # In this case Google will count a full-wide char
                # at least 2 times larger than a half-wide char.
                # It will certainly exceed the limit of the size_per_trans.
                # Causing a googletrans internal jsondecode error.
                size = size + wcswidth_text * 2
            else:
                size = size + len(text)
            if size > size_per_trans:
                # use size_per_trans to split the list
                partial_index.append(i)
                size = 0
        else:
            if is_last:
                is_last = text
                valid_index.append(i)
                # valid_index for valid text position end
        i = i + 1
    if size:
        partial_index.append(i)
        # python sequence
        # every group's end index
    else:
        return None

    len_valid_index = len(valid_index)

    if len_valid_index % 2:
        valid_index.append(i)
        # valid_index for valid text position end

    widgets = [_("Translation: "),
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
        translator = googletrans.Translator(
            user_agent=user_agent,
            service_urls=service_urls)

        for index in partial_index:
            content_to_trans = '\n'.join(text_list[i:index])
            if drop_override_codes:
                content_to_trans = "".join(re.compile(r'{.*?}').split(content_to_trans))
            translation = translator.translate(text=content_to_trans,
                                               dest=dst_language,
                                               src=src_language)
            result_text = translation.text.replace('’', '\'')
            result_list = result_text.split('\n')
            k = 0
            len_result_list = len(result_list)
            while i < index and j < len_valid_index and k < len_result_list:
                if not result_list[k]:
                    # if the result is invalid,
                    # continue
                    k = k + 1
                    continue
                if i < valid_index[j]:
                    # if text is invalid,
                    # append the empty string
                    # and then continue
                    translated_text.append("")
                    i = i + 1
                    pbar.update(i)
                    continue
                if i < valid_index[j + 1]:
                    # if text is valid, append it
                    translated_text.append(result_list[k])
                    k = k + 1
                    i = i + 1
                else:
                    j = j + 2
                pbar.update(i)
            if len(partial_index) > 1:
                time.sleep(sleep_seconds)

        i = valid_index[-1]
        while i < partial_index[-1]:
            # if valid_index[-1] is less than partial_index[-1]
            # add empty strings
            translated_text.append("")
            i = i + 1

        pbar.finish()

    except KeyboardInterrupt:
        pbar.finish()
        print(_("Cancelling translation."))
        return 1

    return translated_text


def list_to_sub_str(
        timed_text,
        fps=30.0,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT):
    """
    Give an input timed text list, format it to a string.
    """

    if subtitles_file_format in ('srt', 'tmp', 'ass', 'ssa'):
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None)
        formatted_subtitles = pysubs2_obj.to_string(
            format_=subtitles_file_format)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = sub_utils.list_to_vtt_str(
            subtitles=timed_text)

    elif subtitles_file_format == 'json':
        formatted_subtitles = sub_utils.list_to_json_str(
            subtitles=timed_text)

    elif subtitles_file_format == 'ass.json':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None)
        formatted_subtitles = pysubs2_obj.to_string(
            format_='json')

    elif subtitles_file_format == 'txt':
        formatted_subtitles = sub_utils.list_to_txt_str(
            subtitles=timed_text)

    elif subtitles_file_format == 'sub':
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None)
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
            style_name=None)
        formatted_subtitles = pysubs2_obj.to_string(
            format_='mpl2',
            fps=fps)

    else:
        # fallback process
        print(_("Format \"{fmt}\" not supported. "
                "Use \"{default_fmt}\" instead.").format(
                    fmt=subtitles_file_format,
                    default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        pysubs2_obj = pysubs2.SSAFile()
        sub_utils.pysubs2_ssa_event_add(
            src_ssafile=None,
            dst_ssafile=pysubs2_obj,
            text_list=timed_text,
            style_name=None)
        formatted_subtitles = pysubs2_obj.to_string(
            format_=constants.DEFAULT_SUBTITLES_FORMAT)

    return formatted_subtitles


def ssafile_to_sub_str(
        ssafile,
        fps=30.0,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT):
    """
    Give an input SSAFile, format it to a string.
    """

    if subtitles_file_format in ('srt', 'tmp', 'ass', 'ssa'):
        formatted_subtitles = ssafile.to_string(
            format_=subtitles_file_format)

    elif subtitles_file_format == 'vtt':
        formatted_subtitles = sub_utils.assfile_to_vtt_str(
            subtitles=ssafile)

    elif subtitles_file_format == 'json':
        formatted_subtitles = sub_utils.assfile_to_json_str(
            subtitles=ssafile)

    elif subtitles_file_format == 'ass.json':
        formatted_subtitles = ssafile.to_string(
            format_='json')

    elif subtitles_file_format == 'txt':
        formatted_subtitles = sub_utils.assfile_to_txt_str(
            subtitles=ssafile)

    elif subtitles_file_format == 'sub':
        formatted_subtitles = ssafile.to_string(
            format_='microdvd',
            fps=fps)
        # sub format need fps
        # ref https://pysubs2.readthedocs.io/en/latest
        # /api-reference.html#supported-input-output-formats

    elif subtitles_file_format == 'mpl2.txt':
        formatted_subtitles = ssafile.to_string(
            format_='mpl2',
            fps=fps)

    else:
        # fallback process
        print(_("Format \"{fmt}\" not supported. "
                "Use \"{default_fmt}\" instead.").format(
                    fmt=subtitles_file_format,
                    default_fmt=constants.DEFAULT_SUBTITLES_FORMAT))
        formatted_subtitles = ssafile.to_string(
            format_=constants.DEFAULT_SUBTITLES_FORMAT)

    return formatted_subtitles


def list_to_ass_str(
        text_list,
        styles_list,
        subtitles_file_format=constants.DEFAULT_SUBTITLES_FORMAT,
        same_event_type=0):
    """
    Give an input timed text list, format it to an ass string.
    """
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
        src_obj = pysubs2_obj
        pysubs2_obj = pysubs2.SSAFile()
        if len(styles_list) == 1:
            sub_utils.pysubs2_ssa_event_add(
                src_ssafile=src_obj,
                dst_ssafile=pysubs2_obj,
                text_list=text_list[1],
                style_name=styles_list[0],
                same_event_type=same_event_type)
        else:
            sub_utils.pysubs2_ssa_event_add(
                src_ssafile=src_obj,
                dst_ssafile=pysubs2_obj,
                text_list=text_list[1],
                style_name=styles_list[2],
                same_event_type=same_event_type)

    if subtitles_file_format != 'ass.json':
        formatted_subtitles = pysubs2_obj.to_string(format_=subtitles_file_format)
    else:
        formatted_subtitles = pysubs2_obj.to_string(format_='json')

    return formatted_subtitles


def str_to_file(
        str_,
        output,
        input_m=input):
    """
    Give a string and write it to file
    """
    dest = output

    if input_m:
        while os.path.isfile(dest):
            print(_("There is already a file with the same name "
                    "in this location: \"{dest_name}\".").format(dest_name=dest))
            dest = input_m(
                _("Input a new path (including directory and file name) for output file.\n"))
            ext = os.path.splitext(dest)[-1]
            dest = os.path.splitext(dest)[0]
            dest = "{base}{ext}".format(base=dest,
                                        ext=ext)

    with open(dest, 'wb') as output_file:
        output_file.write(str_.encode("utf-8"))

    return dest
