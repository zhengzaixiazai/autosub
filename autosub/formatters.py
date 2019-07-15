#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines subtitle formatters used by autosub.
"""

from __future__ import absolute_import, unicode_literals

import json
import pysubs2


def pysubs2_formatter(subtitles,
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
        for ((start, end), text) in subtitles:
            event = pysubs2.SSAEvent()
            event.start = start
            event.end = end
            event.text = text
            event.style = style_name
            pysubs2_obj.events.append(event)
    else:
        for ((start, end), text) in subtitles:
            event = pysubs2.SSAEvent()
            event.start = start
            event.end = end
            event.text = text
            pysubs2_obj.events.append(event)
    return pysubs2_obj.to_string(format_=sub_format, fps=pysubs2_obj.fps)


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
