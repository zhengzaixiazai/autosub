#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines subtitle formatters used by autosub.
"""
# Import built-in modules
import wave
import json
import gettext

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import constants


SUB_UTILS_TEXT = gettext.translation(domain=__name__,
                                     localedir=constants.LOCALE_PATH,
                                     languages=[constants.CURRENT_LOCALE],
                                     fallback=True)

_ = SUB_UTILS_TEXT.gettext


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
                    event.is_comment = src_ssafile.events[i].is_comment
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
                        event.is_comment = src_ssafile.events[i].is_comment
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
                        event.is_comment = src_ssafile.events[i].is_comment
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
                        event.is_comment = src_ssafile.events[i].is_comment
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
                        event.is_comment = src_ssafile.events[i].is_comment
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


def merge_bilingual_assfile(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        subtitles,
        order=1):
    """
    Merge a bilingual subtitles file's events automatically.
    """
    style_events = {}
    event_pos = {}

    i = 0
    for event in subtitles.events:
        if event.style not in style_events:
            style_events[event.style] = [event]
            event_pos[event.style] = i
        else:
            style_events[event.style].append(event)
        i = i + 1

    sorted_events_list = sorted(style_events.values(), key=len)
    events_1 = sorted_events_list.pop()
    events_2 = sorted_events_list.pop()

    dst_ssafile = pysubs2.SSAFile()
    src_ssafile = pysubs2.SSAFile()

    if event_pos[events_1[0].style] > event_pos[events_2[0].style] and order:
        # destination language events are behind source language events in a bilingual subtitles
        dst_ssafile.events = events_1
        src_ssafile.events = events_2
    else:
        dst_ssafile.events = events_2
        src_ssafile.events = events_1

    dst_ssafile.sort()
    src_ssafile.sort()

    new_ssafile = pysubs2.SSAFile()
    new_ssafile.styles = subtitles.styles
    new_ssafile.info = subtitles.info

    # default in dst-lf-src order
    dst_length = len(dst_ssafile.events)
    src_length = len(src_ssafile.events)
    i = 0
    j = 0

    start = 0
    end = 0

    events_0 = []
    while i < dst_length and j < src_length:
        if dst_ssafile.events[i].is_comment != src_ssafile.events[j].is_comment:
            if dst_ssafile.events[i].is_comment:
                events_0.append(dst_ssafile.events[i])
                i = i + 1
                continue
            events_0.append(src_ssafile.events[j])
            j = j + 1
            continue
        if dst_ssafile.events[i].start == src_ssafile.events[j].start or \
                dst_ssafile.events[i].end == src_ssafile.events[j].end:
            start = dst_ssafile.events[i].start
            end = dst_ssafile.events[i].end
        elif dst_ssafile.events[i].start >= src_ssafile.events[j].end:
            events_0.append(src_ssafile.events[j])
            j = j + 1
            continue
        elif src_ssafile.events[j].start >= dst_ssafile.events[i].end:
            events_0.append(dst_ssafile.events[i])
            i = i + 1
            continue
        elif src_ssafile.events[j].start < dst_ssafile.events[i].start:
            event = pysubs2.SSAEvent()
            event.start = src_ssafile.events[j].start
            event.end = dst_ssafile.events[i].start
            event.is_comment = src_ssafile.events[j].is_comment
            event.text = src_ssafile.events[j].text
            event.style = src_ssafile.events[j].style
            events_0.append(event)
            start = dst_ssafile.events[i].start

            if src_ssafile.events[j].end > dst_ssafile.events[i].end:
                event = pysubs2.SSAEvent()
                event.start = dst_ssafile.events[i].end
                event.end = src_ssafile.events[j].end
                event.is_comment = src_ssafile.events[j].is_comment
                event.text = src_ssafile.events[j].text
                event.style = src_ssafile.events[j].style
                events_0.append(event)
                end = dst_ssafile.events[i].end
            else:
                end = src_ssafile.events[j].end

        elif dst_ssafile.events[i].start < src_ssafile.events[j].start:
            event = pysubs2.SSAEvent()
            event.start = dst_ssafile.events[i].start
            event.end = src_ssafile.events[j].start
            event.is_comment = dst_ssafile.events[i].is_comment
            event.text = dst_ssafile.events[i].text
            event.style = dst_ssafile.events[i].style
            events_0.append(event)
            start = src_ssafile.events[j].start

            if dst_ssafile.events[i].end > src_ssafile.events[j].end:
                event = pysubs2.SSAEvent()
                event.start = src_ssafile.events[j].end
                event.end = dst_ssafile.events[i].end
                event.is_comment = dst_ssafile.events[i].is_comment
                event.text = dst_ssafile.events[i].text
                event.style = dst_ssafile.events[i].style
                events_0.append(event)
                end = src_ssafile.events[j].end
            else:
                end = dst_ssafile.events[i].end

        event = pysubs2.SSAEvent()
        event.start = start
        event.end = end
        event.is_comment = dst_ssafile.events[i].is_comment
        event.text = \
            dst_ssafile.events[i].text + \
            "\\N{{\\r{style_name}}}".format(
                style_name=src_ssafile.events[j].style) + \
            src_ssafile.events[j].text
        event.style = dst_ssafile.events[i].style
        new_ssafile.events.append(event)
        i = i + 1
        j = j + 1

    if i < dst_length:
        new_ssafile.events = new_ssafile.events + events_0 + dst_ssafile.events[i:]
    else:
        new_ssafile.events = new_ssafile.events + events_0 + src_ssafile.events[j:]

    for events in sorted_events_list:
        if event_pos[events[0].style] > event_pos[new_ssafile.events[0].style]:
            new_ssafile.events = new_ssafile.events + events
        else:
            new_ssafile.events = events + new_ssafile.events

    return new_ssafile


def merge_src_assfile(  # pylint: disable=too-many-locals, too-many-nested-blocks,
        # pylint: disable=too-many-statements, too-many-branches
        subtitles,
        max_join_size=constants.DEFAULT_MAX_SIZE_PER_EVENT,
        max_delta_time=int(constants.DEFAULT_CONTINUOUS_SILENCE * 1000),
        delimiters=constants.DEFAULT_EVENT_DELIMITER
):
    """
    Merge a source subtitles file's events automatically.
    """
    new_ssafile = pysubs2.SSAFile()
    new_ssafile.styles = subtitles.styles
    new_ssafile.info = subtitles.info
    style_events = {}

    for event in subtitles.events:
        if event.style not in style_events:
            style_events[event.style] = [event]
        else:
            style_events[event.style].append(event)

    sorted_events_list = sorted(style_events.values(), key=len)
    events_1 = sorted_events_list.pop()

    temp_ssafile = pysubs2.SSAFile()
    temp_ssafile.events = events_1
    temp_ssafile.sort()

    sub_length = len(temp_ssafile.events)
    i = 1
    j = 0
    k = 0

    new_ssafile.events.append(temp_ssafile.events[0])

    while i < sub_length - 1:
        if len(new_ssafile.events[-1].text) < max_join_size:
            if not new_ssafile.events[-1].is_comment and not temp_ssafile.events[i].is_comment\
                    and new_ssafile.events[-1].style == temp_ssafile.events[i].style\
                    and temp_ssafile.events[i].start\
                    - new_ssafile.events[-1].end < max_delta_time \
                    and new_ssafile.events[-1].text.rstrip(" ")[-1] not in delimiters:
                if len(new_ssafile.events[-1].text) + \
                        len(temp_ssafile.events[i].text) < max_join_size:
                    new_ssafile.events[-1].end = temp_ssafile.events[i].end
                    if new_ssafile.events[-1].text[-1] != " ":
                        new_ssafile.events[-1].text = new_ssafile.events[-1].text + " " + \
                                                      temp_ssafile.events[i].text
                    else:
                        new_ssafile.events[-1].text = \
                            new_ssafile.events[-1].text + temp_ssafile.events[i].text
                    j = j + 1

                else:
                    combination = new_ssafile.events[-1].text + " " + temp_ssafile.events[i].text
                    min_range = int(len(combination) * 0)
                    max_range = len(combination) - min_range
                    half_pos = int(len(combination) / 2)
                    word_dict = get_slice_pos_dict(combination, delimiters=delimiters)
                    # use punctuations to split the sentence first
                    if len(word_dict) <= 1:
                        word_dict = get_slice_pos_dict(combination)
                    word_set = set(word_dict.keys())
                    stop_word_set = constants.DEFAULT_ENGLISH_STOP_WORDS_SET & word_set
                    last_index = 0
                    last_delta = half_pos - last_index
                    if stop_word_set:
                        for stop_word in stop_word_set:
                            for index in word_dict[stop_word]:
                                if min_range < index < max_range:
                                    delta = abs(index - half_pos)
                                    if delta < last_delta:
                                        last_index = index
                                        last_delta = delta
                    if last_index and last_index < max_join_size:
                        joint_event = join_event(new_ssafile.events[-1], temp_ssafile.events[i])
                        new_ssafile.events.pop()
                        new_ssafile.events.extend(split_event(joint_event, last_index))
                        k = k + 1

                i = i + 1
                continue

        new_ssafile.events.append(temp_ssafile.events[i])
        i = i + 1

    for events in sorted_events_list:
        new_ssafile.events = events + new_ssafile.events

    print(_("Merge {count} lines of events.").format(count=j))
    print(_("Split {count} lines of events.").format(count=k))
    print(_("Reduce {count} lines of events.").format(count=j - k))

    return new_ssafile


def get_slice_pos_dict(
        sentence,
        delimiters=" "
):
    """
    Get word position dictionary from sentence.
    """
    i = 0
    j = 0
    result_dict = {}
    length = len(sentence)
    while i < length:
        if sentence[i] in delimiters:
            if i != j and sentence[j:i].strip(" "):
                index = result_dict.get(sentence[j:i])
                if not index:
                    result_dict[sentence[j:i]] = [j]
                else:
                    result_dict[sentence[j:i]].append(j)
            j = i + 1
        i = i + 1

    return result_dict


def join_event(
        event1,
        event2
):
    """
    Join two events.
    """
    joint_event = event1.copy()
    joint_event.start = event1.start
    joint_event.end = event2.end
    joint_event.text = event1.text + " " + event2.text

    return joint_event


def split_event(
        event,
        position
):
    """
    Split an event based on position.
    """
    ratio = position / len(event.text)
    first_event = event.copy()
    first_event.start = event.start
    first_event.end = int((event.end - event.start) * ratio) + event.start
    first_event.text = event.text[:position].rstrip(" ")

    second_event = event.copy()
    second_event.end = event.end
    second_event.start = first_event.end
    second_event.text = event.text[position:]

    return [first_event, second_event]
