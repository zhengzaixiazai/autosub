#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines subtitle formatters used by autosub.
"""
# Import built-in modules
from __future__ import absolute_import, unicode_literals
import wave
import json

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import constants


def sub_to_speech_regions(
        audio_wav,
        sub_file,
        ext_max_size_ms=constants.MAX_REGION_SIZE_LIMIT * 1000):
    """
    Give an input audio_wav file and subtitles file and generate proper speech regions.
    """
    regions = []
    reader = wave.open(audio_wav)
    audio_file_length = int(float(reader.getnframes()) / float(reader.getframerate())) * 1000
    reader.close()

    ext_regions = pysubs2.SSAFile.load(sub_file)

    for event in ext_regions.events:
        if not event.is_comment:
            # not a comment region
            if event.start > audio_file_length:
                # even later than the source file length
                continue
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

    return regions


def pysubs2_ssa_event_add(  # pylint: disable=too-many-branches, too-many-statements
        src_ssafile,
        dst_ssafile,
        text_list,
        style_name,
        same_event_type=0,):
    """
    Serialize a list of subtitles using pysubs2.
    """
    if not style_name:
        style_name = 'Default'
    if text_list:
        if not src_ssafile:
            if isinstance(text_list[0][0], tuple):
                # text_list is [((start, end), text), ...]
                # text_list provides regions
                for ((start, end), text) in text_list:
                    event = pysubs2.SSAEvent()
                    event.start = start
                    event.end = end
                    event.text = text
                    event.style = style_name
                    dst_ssafile.events.append(event)
            elif isinstance(text_list[0][0], int):
                # text_list is [(start, end), ...]
                # text_list provides regions only
                for start, end in text_list:
                    event = pysubs2.SSAEvent()
                    event.start = start
                    event.end = end
                    event.style = style_name
                    dst_ssafile.events.append(event)
        else:
            # if src_ssafile exist
            # src_ssafile provides regions
            # text_list is [text, text, ...]
            i = 0
            length = len(text_list)
            if same_event_type == 0:
                #  append text_list to new events
                while i < length:
                    event = pysubs2.SSAEvent()
                    event.start = src_ssafile.events[i].start
                    event.end = src_ssafile.events[i].end
                    event.text = text_list[i]
                    event.style = style_name
                    dst_ssafile.events.append(event)
                    i = i + 1
            elif same_event_type == 1:
                # add text_list to src_ssafile
                # before the existing text in event
                if src_ssafile.events[0].style == style_name:
                    # same style
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.text = \
                            text_list[i] + "\\N" + src_ssafile.events[i].text
                        event.style = style_name
                        dst_ssafile.events.append(event)
                        i = i + 1
                else:
                    # different style
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.text = \
                            text_list[i] + \
                            "\\N{{\\r{style_name}}}".format(
                                style_name=src_ssafile.events[i].style) + \
                            src_ssafile.events[i].text
                        event.style = style_name
                        dst_ssafile.events.append(event)
                        i = i + 1
            elif same_event_type == 2:
                # add text_list to src_ssafile
                # after the existing text in event
                if src_ssafile.events[0].style == style_name:
                    # same style
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.text = \
                            src_ssafile.events[i].text + "\\N" + text_list[i]
                        event.style = style_name
                        dst_ssafile.events.append(event)
                        i = i + 1
                else:
                    # different style
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.text = \
                            src_ssafile.events[i].text + \
                            "\\N{{\\r{style_name}}}".format(
                                style_name=style_name) + \
                            text_list[i]
                        event.style = style_name
                        dst_ssafile.events.append(event)
                        i = i + 1
    else:
        # src_ssafile provides regions only
        i = 0
        length = len(src_ssafile.events)
        while i < length:
            event = pysubs2.SSAEvent()
            event.start = src_ssafile.events[i].start
            event.end = src_ssafile.events[i].end
            event.style = style_name
            dst_ssafile.events.append(event)
            i = i + 1


def list_to_vtt_str(subtitles):
    """
    Serialize a list of subtitles according to the VTT format.
    """
    pysubs2_obj = pysubs2.SSAFile()
    pysubs2_ssa_event_add(
        src_ssafile=None,
        dst_ssafile=pysubs2_obj,
        text_list=subtitles,
        style_name=None)
    formatted_subtitles = pysubs2_obj.to_string(
        format_='srt')
    i = 0
    lines = formatted_subtitles.split('\n')
    new_lines = []
    for line in lines:
        if i % 4 == 1:
            line = line.replace(',', '.')
        new_lines.append(line)
        i = i + 1
    formatted_subtitles = '\n'.join(new_lines)
    formatted_subtitles = 'WEBVTT\n\n' + formatted_subtitles
    return formatted_subtitles


def assfile_to_vtt_str(subtitles):
    """
    Serialize ASSFile according to the VTT format.
    """
    formatted_subtitles = subtitles.to_string(
        format_='srt')
    i = 0
    lines = formatted_subtitles.split('\n')
    new_lines = []
    for line in lines:
        if i % 4 == 1:
            line = line.replace(',', '.')
        new_lines.append(line)
        i = i + 1
    formatted_subtitles = '\n'.join(new_lines)
    formatted_subtitles = 'WEBVTT\n\n' + formatted_subtitles
    return formatted_subtitles


def list_to_json_str(subtitles):
    """
    Serialize a list of subtitles as a JSON blob.
    """
    if isinstance(subtitles[0][0], tuple):
        # text_list is [((start, end), text), ...]
        # text_list provides regions
        subtitle_dicts = [
            {
                'start': start / 1000.0,
                'end': end / 1000.0,
                'content': text
            }
            for ((start, end), text)
            in subtitles
        ]
    else:
        # text_list is [(start, end), ...]
        # text_list provides regions only
        subtitle_dicts = [
            {
                'start': start / 1000.0,
                'end': end / 1000.0
            }
            for start, end
            in subtitles
        ]
    return json.dumps(subtitle_dicts, indent=4, ensure_ascii=False)


def assfile_to_json_str(subtitles):
    """
    Serialize ASSFile as a JSON blob.
    """
    subtitle_dicts = [
        {
            'start': event.start / 1000.0,
            'end': event.end / 1000.0,
            'content': event.text
        }
        for event
        in subtitles.events
    ]
    return json.dumps(subtitle_dicts, indent=4, ensure_ascii=False)


def list_to_txt_str(subtitles):
    """
    Serialize a list of subtitles as a newline-delimited string.
    """
    if isinstance(subtitles[0][0], tuple):
        # text_list is [((start, end), text), ...]
        # text_list provides regions
        return '\n'.join(text for (_rng, text) in subtitles)

    # text_list is [(start, end), ...]
    # text_list provides regions only
    result = ""
    for start, end in subtitles:
        line = "{start} {end}".format(
            start=start / 1000.0,
            end=end / 1000.0)
        result = result + '\n' + line
    return result


def assfile_to_txt_str(subtitles):
    """
    Serialize ASSFile as a newline-delimited string.
    """
    return '\n'.join(event.text for event in subtitles.events)
