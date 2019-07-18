#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines subtitle formatters used by autosub.
"""

from __future__ import absolute_import, unicode_literals

# Import built-in modules
import os
import wave
import json

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import constants
from autosub import ffmpeg_utils


def sub_to_speech_regions(
        source_file,
        sub_file,
        ffmpeg_cmd="ffmpeg",
        ext_max_size_ms=constants.MAX_EXT_REGION_SIZE * 1000
):
    """
    Give an input audio/video file and subtitles file, generate proper speech regions.
    """
    regions = []
    audio_wav = ffmpeg_utils.source_to_audio(
        source_file,
        ffmpeg_cmd=ffmpeg_cmd)
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


def pysubs2_formatter(timed_text,
                      sub_format='srt',
                      fps=0.0):
    """
    Serialize a list of timed_text according to the SRT format.
    """
    pysubs2_obj = pysubs2.SSAFile()
    if fps != 0.0:
        pysubs2_obj.fps = fps
    for ((start, end), text) in timed_text:
        event = pysubs2.SSAEvent()
        event.start = start
        event.end = end
        event.text = text
        pysubs2_obj.events.append(event)
    return pysubs2_obj.to_string(format_=sub_format, fps=pysubs2_obj.fps)


def pysubs2_ssa_event_add(
        src_ssafile,
        dst_ssafile,
        text_list,
        style_name,
):
    """
    Serialize a list of subtitles according to the SRT format.
    """
    if text_list:
        if not src_ssafile and isinstance(text_list[0], tuple):
            # text_list is [((start, end), text), ...]
            # text_list provides regions
            for ((start, end), text) in text_list:
                event = pysubs2.SSAEvent()
                event.start = start
                event.end = end
                event.text = text
                event.style = style_name
                dst_ssafile.events.append(event)
        elif src_ssafile:
            # text_list is [text, ...]
            # src_ssafile provides regions
            i = 0
            for text in text_list:
                event = pysubs2.SSAEvent()
                event.start = src_ssafile.events[i].start
                event.end = src_ssafile.events[i].end
                event.text = text
                event.style = style_name
                dst_ssafile.events.append(event)
                i = i + 1
        else:
            # text_list provides regions only
            for start, end in text_list:
                event = pysubs2.SSAEvent()
                event.start = start
                event.end = end
                event.style = style_name
                dst_ssafile.events.append(event)
    else:
        # src_ssafile provides regions only
        for src_event in src_ssafile.events.copy():
            event = pysubs2.SSAEvent()
            event.start = src_event.start
            event.end = src_event.end
            event.style = style_name
            dst_ssafile.events.append(event)
    return dst_ssafile


def vtt_formatter(subtitles):
    """
    Serialize a list of subtitles according to the VTT format.
    """
    text = pysubs2_formatter(subtitles)
    text = 'WEBVTT\n\n' + text.replace(',', '.')
    return text


def json_formatter(subtitles):
    """
    Serialize a list of subtitles as a JSON blob.
    """
    subtitle_dicts = [
        {
            'start': start / 1000.0,
            'end': end / 1000.0,
            'content': text
        }
        for ((start, end), text)
        in subtitles
    ]
    return json.dumps(subtitle_dicts, indent=4, ensure_ascii=False)


def txt_formatter(subtitles):
    """
    Serialize a list of subtitles as a newline-delimited string.
    """
    return '\n'.join(text for (_rng, text) in subtitles)


def pysubs2_times_formatter(times,
                            sub_format='srt',
                            fps=0.0,
                            ass_styles=None):
    """
    Serialize a list of subtitles according to the SRT format.
    """
    pysubs2_obj = pysubs2.SSAFile()
    if fps != 0.0:
        pysubs2_obj.fps = fps
    if ass_styles:
        pysubs2_obj.styles = ass_styles
        style_name = ass_styles.popitem()[0]
        for (start, end) in times:
            event = pysubs2.SSAEvent()
            event.start = start
            event.end = end
            event.style = style_name
            pysubs2_obj.events.append(event)
    else:
        for (start, end) in times:
            event = pysubs2.SSAEvent()
            event.start = start
            event.end = end
            pysubs2_obj.events.append(event)
    return pysubs2_obj.to_string(format_=sub_format, fps=pysubs2_obj.fps)


def vtt_times_formatter(times):
    """
    Serialize a list of subtitles according to the VTT format.
    """
    text = pysubs2_times_formatter(times)
    text = 'WEBVTT\n\n' + text.replace(',', '.')
    return text


def json_times_formatter(times):
    """
    Serialize a list of subtitles as a JSON blob.
    """
    subtitle_dicts = [
        {
            'start': start / 1000.0,
            'end': end / 1000.0
        }
        for (start, end)
        in times
    ]
    return json.dumps(subtitle_dicts, indent=4, ensure_ascii=False)
