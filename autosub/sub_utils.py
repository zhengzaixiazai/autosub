#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines subtitle formatters used by autosub.
"""
# pylint: disable=too-many-lines
# Import built-in modules
import wave
import json
import gettext
import os
import string
import copy
import re

# Import third-party modules
import pysubs2
from fuzzywuzzy import fuzz

# Any changes to the path and your own modules
from autosub import constants

SUB_UTILS_TEXT = gettext.translation(domain=__name__,
                                     localedir=constants.LOCALE_PATH,
                                     languages=[constants.CURRENT_LOCALE],
                                     fallback=True)

_ = SUB_UTILS_TEXT.gettext


def str_to_file(
        str_,
        output,
        input_m=input,
        encoding=constants.DEFAULT_ENCODING):
    """
    Give a string and write it to file
    """
    dest = output
    ext = os.path.splitext(dest)[-1]

    if input_m:
        if not os.path.isdir(os.path.dirname(dest)):
            dest = os.getcwd() + os.sep + os.path.basename(dest)

        while os.path.isfile(dest):
            old_dest = dest
            print(_("There is already a file with the same path "
                    "or the path isn't valid: \"{dest_name}\".").format(dest_name=dest))
            dest = input_m(
                _("Input a new path (including directory and file name) for output file.\n"))
            if dest == "":
                dest = old_dest
                continue
            dest = dest.rstrip("\"").lstrip("\"")
            if not os.path.isdir(os.path.dirname(dest)):
                dest = os.getcwd() + os.sep + os.path.basename(dest)
            dest = os.path.splitext(dest)[0]
            dest = "{base}{ext}".format(base=dest,
                                        ext=ext)

    with open(dest, 'wb') as output_file:
        output_file.write(str_.encode(encoding))
    return dest


class VTTWord:  # pylint: disable=too-few-public-methods
    """
    Class for youtube WebVTT word and word-level timestamp.
    """

    def __init__(self,
                 start=0,
                 end=0,
                 word=""):
        self.start = start
        self.end = end
        self.word = word

    @property
    def duration(self):
        """
        Subtitle duration in milliseconds (read/write property).

        Writing to this property adjusts :attr:`SSAEvent.end`.
        Setting negative durations raises :exc:`ValueError`.
        """
        return self.end - self.start

    @duration.setter
    def duration(self, mili_sec):
        if mili_sec >= 0:
            self.end = self.start + mili_sec
        else:
            raise ValueError("Subtitle duration cannot be negative")

    @property
    def speed(self):
        """
        Subtitle speed in char per second (read/write property).
        """
        if self.end > self.start and self.word:
            speed = len(self.word) * 1000 // (self.end - self.start)
        else:
            speed = 10
        return speed

    @speed.setter
    def speed(self, char_per_sec):
        if char_per_sec <= 0:
            char_per_sec = 10
        self.duration = len(self.word) * 1000 // char_per_sec


def split_vtt_word(vtt_word):
    """
    Strip space in word and return a list of VTTWord
    """
    word_list = vtt_word.word.split()
    vtt_word_list = []
    if len(word_list) > 1:
        start = vtt_word.start
        end = vtt_word.end
        if end == 0:
            vtt_word.speed = 10
        for sub_word in word_list[:-1]:
            temp = int(len(sub_word) / vtt_word.speed * 1000)
            vtt_word_list.append(VTTWord(start=start, end=temp, word=sub_word))
            start = temp
        vtt_word_list.append(VTTWord(start=start, end=end, word=word_list[-1]))
    else:
        vtt_word_list.append(vtt_word)

    return vtt_word_list


def find_split_vtt_word(
        total_length,
        stop_word_set,
        vtt_word_dict,
        min_range_ratio
):
    """
    Find index to split vtt_word_dict.
    """
    half_pos = int(total_length / 2)
    min_range = int(min_range_ratio * total_length)
    max_range = total_length - min_range
    last_index = (0, 0)
    last_delta = half_pos - last_index[1]
    if stop_word_set:
        for stop_word in stop_word_set:
            for index in vtt_word_dict[stop_word]:
                if min_range < index[1] < max_range:
                    delta = abs(index[1] - half_pos)
                    if delta < last_delta:
                        last_index = index
                        last_delta = delta

    return last_index


def get_vtt_slice_pos_dict(
        vtt_words,
):
    """
    Get word position dictionary from vtt_words.
    """
    vtt_word_dict = {}
    i = 0
    length = len(vtt_words)
    j = 0
    while i < length:
        key_ = vtt_word_dict.get(vtt_words[i].word)
        if not key_:
            # first for vtt_word list index
            # second for string index
            vtt_word_dict[vtt_words[i].word] = [(i, j)]
        else:
            vtt_word_dict[vtt_words[i].word].append((i, j))
        j = j + len(vtt_words[i].word)
        i = i + 1

    return vtt_word_dict


class YTBWebVTT:  # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-arguments, too-many-statements, too-many-locals
    """
    Class for youtube WebVTT.
    """

    def __init__(self):
        self.vtt_words = []
        self.vtt_words_index = []
        self.path = ""

    @classmethod
    def from_file(cls,
                  path,
                  encoding="utf-8"):
        """
        Get youtube WebVTT from a file.
        """
        subs = cls()
        subs.path = path
        last_timestamp = None
        j = 0
        file_p = open(path, encoding=encoding)
        line_list = file_p.readlines()
        line_list = line_list[4:]
        file_p.close()
        is_content_outside_angle = True
        word = ""
        for line in line_list:
            line = line.rstrip()
            if not line:
                continue
            stamps = constants.VTT_TIMESTAMP.findall(line)
            if len(stamps) == 1 and len(stamps[0]) == 2:
                # youtube WebVTT sentence timestamp line
                last_timestamp = pysubs2.time.TIMESTAMP.findall(stamps[0][0])[0]
            else:
                stamps = constants.VTT_WORD_TIMESTAMP.findall(line)
                if stamps:  # youtube WebVTT word-level timestamp
                    stamps.insert(0, last_timestamp)
                    stamp_ms = []
                    for stamp in stamps:
                        stamp_ms.append(pysubs2.time.timestamp_to_ms(stamp))
                    if subs.vtt_words:
                        subs.vtt_words[-1].end = stamp_ms[0]
                    try:
                        # todo2: need regex
                        j = 0
                        for char in line:
                            if char == '>':
                                is_content_outside_angle = True
                                continue
                            if char == '<':
                                is_content_outside_angle = False
                                if word:
                                    start = stamp_ms[j]
                                    if j < len(stamp_ms) - 1:
                                        end = stamp_ms[j + 1]
                                    else:
                                        end = 0
                                    subs.vtt_words.extend(split_vtt_word(VTTWord(
                                        word=word.lstrip().rstrip(), start=start, end=end)))
                                    j = j + 1
                                    word = ""
                                continue
                            if is_content_outside_angle:
                                word = word + char
                    except ValueError:
                        pass
                else:
                    text = line.split()
                    if len(text) == 1:
                        if subs.vtt_words:
                            if text[0] != subs.vtt_words[-1].word:
                                vtt_word = VTTWord(word=text[0].lstrip().rstrip())
                                if not subs.vtt_words[-1].end:
                                    subs.vtt_words[-1].end = \
                                        pysubs2.time.timestamp_to_ms(last_timestamp)
                                vtt_word.start = subs.vtt_words[-1].end
                                vtt_word.speed = subs.vtt_words[-1].speed
                                subs.vtt_words.append(vtt_word)
                        else:
                            vtt_word = VTTWord(word=text[0].lstrip().rstrip())
                            vtt_word.start = pysubs2.time.timestamp_to_ms(last_timestamp)
                            vtt_word.speed = 10
                            subs.vtt_words.append(vtt_word)
        if len(subs.vtt_words) > 1:
            last_speed = subs.vtt_words[-2].speed
        else:
            last_speed = 10
        subs.vtt_words[-1].speed = last_speed
        return subs

    def text_to_ass_events(self,
                           events,
                           key_tag="",
                           style_name="default",
                           is_cap=False):
        """
        Simply export to ass events.
        """
        if not self.vtt_words_index:
            return events
        i = 0
        j = 0
        if key_tag:
            for event in events:
                if is_cap:
                    event.text = "{{{key_tag}{time}}}{word} ".format(
                        key_tag=key_tag,
                        time=int(self.vtt_words[j].duration // 10),
                        word=self.vtt_words[j].word[0].upper() + self.vtt_words[j].word[1:])
                    event.style = style_name
                    j = j + 1
                while j < self.vtt_words_index[i]:
                    event.text = "{event}{{{key_tag}{time}}}{word} ".format(
                        event=event.text,
                        key_tag=key_tag,
                        time=int(self.vtt_words[j].duration // 10),
                        word=self.vtt_words[j].word)
                    event.style = style_name
                    j = j + 1
                if is_cap:
                    event.text = event.text[:-1] + "."
                i = i + 1
        else:
            for event in events:
                if is_cap:
                    event.text = "{word} ".format(
                        word=self.vtt_words[j].word[0].upper() + self.vtt_words[j].word[1:])
                    event.style = style_name
                    j = j + 1
                while j < self.vtt_words_index[i]:
                    event.text = "{event}{word} ".format(
                        event=event.text,
                        word=self.vtt_words[j].word)
                    event.style = style_name
                    j = j + 1
                if is_cap:
                    event.text = event.text[:-1] + "."
                i = i + 1
        return events

    def to_text_str(self):
        """
        Export to ass text.
        """
        i = 0
        j = 0
        text_str = ""
        if self.vtt_words_index:
            vtt_words_index_len = len(self.vtt_words_index)
            while i < vtt_words_index_len:
                while j < self.vtt_words_index[i]:
                    text_str = "{event}{word} ".format(
                        event=text_str,
                        word=self.vtt_words[j].word)
                    j = j + 1
                text_str = text_str + "\n"
                i = i + 1
        else:
            for vtt_word in self.vtt_words:
                text_str = "{event}{word} ".format(
                    event=text_str,
                    word=vtt_word.word)
        return text_str

    def man_get_vtt_words_index(self):
        """
        Get end timestamps from a SSAEvent list automatically by external regions.
        """
        events = []
        path = self.path[:-3] + "txt"
        path = str_to_file(
            str_=self.to_text_str(),
            output=path,
            input_m=input)
        input(_("Wait for the events manual adjustment. "
                "Press Enter to continue."))
        line_count = 0
        i = 0
        j = 0
        vtt_len = len(self.vtt_words)
        is_paused = False
        trans = str.maketrans(string.punctuation, " " * len(string.punctuation))
        while True:
            file_p = open(path, encoding=constants.DEFAULT_ENCODING)
            line_list = file_p.readlines()
            line_list_len = len(line_list)
            file_p.close()
            k = line_count
            while k < line_list_len:
                word_list = line_list[k].split()
                event = pysubs2.SSAEvent(start=self.vtt_words[i].start)
                word_list_len = len(word_list)
                while j < word_list_len:
                    if self.vtt_words[i].word != word_list[j]:
                        if fuzz.partial_ratio(
                                self.vtt_words[i].word.lower().translate(trans).replace(" ", ""),
                                word_list[j].lower().translate(trans).replace(" ", "")) != 100:
                            if self.vtt_words_index:
                                start_delta = self.vtt_words_index[-1]
                            else:
                                start_delta = 0
                            if i < vtt_len - 5:
                                end_delta = i + 6
                            else:
                                end_delta = vtt_len
                            print(_("\nLine {num}, word {num2}").format(
                                num=len(events), num2=j))
                            cur_line = ""
                            for vtt_word in self.vtt_words[start_delta:end_delta]:
                                cur_line = "{cur_line} {word}".format(cur_line=cur_line,
                                                                      word=vtt_word.word)
                            print(cur_line)
                            print(" ".join(word_list))
                            print("{word} | {word2}".format(
                                word=self.vtt_words[i].word, word2=word_list[j]))
                            result = input(_("Press Enter to manual adjust. "
                                             "Input 1 to overwrite."))
                            if result != "1":
                                line_count = k
                                is_paused = True
                                break

                            self.vtt_words[i].word = word_list[j]
                            is_paused = False
                        else:
                            if is_paused:
                                is_paused = False
                            self.vtt_words[i].word = word_list[j]

                    i = i + 1
                    j = j + 1
                    if i > vtt_len:
                        break
                if is_paused:
                    break
                j = 0
                self.vtt_words_index.append(i)
                if i:
                    event.end = self.vtt_words[i - 1].end
                events.append(event)
                k = k + 1
            if not is_paused:
                break
        constants.DELETE_PATH(path)
        return events

    def auto_get_vtt_words_index(self,
                                 events,
                                 stop_words_set_1,
                                 stop_words_set_2,
                                 text_limit=constants.DEFAULT_MAX_SIZE_PER_EVENT,
                                 avoid_split=False):
        """
        Adjust end timestamps and get SSAEvent events and self.vtt_words_index automatically
        by external regions.
        """
        i = 0
        j = 0
        vtt_words_len = len(self.vtt_words)
        vtt_words_index = [0]
        is_started = False
        # last_len = 0
        text_len = 0
        events_len = len(events)
        while j < vtt_words_len and i < events_len:
            if self.vtt_words[j].start < events[i].end:
                if not is_started:
                    # start_delta = events[i].start - self.vtt_words[j].start
                    # if start_delta < 1000:
                    # inside the event
                    # start_delta < 0
                    # or a little ahead of time
                    # 0 <= start_delta < 300
                    self.vtt_words[j].start = events[i].start
                    if self.vtt_words[j].end <= self.vtt_words[j].start:
                        if j < vtt_words_len - 1:
                            if self.vtt_words[j].start < self.vtt_words[j + 1].start:
                                self.vtt_words[j].end = self.vtt_words[j + 1].start
                            else:
                                delta = \
                                    (self.vtt_words[j + 1].end - self.vtt_words[j].start) >> 1
                                self.vtt_words[j].end = delta + self.vtt_words[j].start
                                self.vtt_words[j + 1].start = delta + self.vtt_words[j].end
                        else:
                            self.vtt_words[j].end = self.vtt_words[j].start + 200
                    is_started = True
                    # else:
                    #     # check if it's necessary to insert new events
                    #     if i < len(events) - 1:
                    #         events.insert(
                    #             i,
                    #             pysubs2.SSAEvent(start=self.vtt_words[j].start,
                    #                              end=events[i].start))
                    #     else:
                    #         events.insert(
                    #             i,
                    #             pysubs2.SSAEvent(start=self.vtt_words[j].start,
                    #                              end=self.vtt_words[j].start + 5000))
                    #     events[i].is_comment = True
                    #     # the end time is estimated so it needs a trim
                    #     continue
                text_len = text_len + len(self.vtt_words[j].word) + 1
                if text_len > text_limit and not avoid_split:
                    vtt_word_dict = get_vtt_slice_pos_dict(
                        self.vtt_words[vtt_words_index[-1]:j])
                    stop_word_set = stop_words_set_1 & set(vtt_word_dict.keys())
                    last_index = find_split_vtt_word(
                        total_length=text_len,
                        stop_word_set=stop_word_set,
                        vtt_word_dict=vtt_word_dict,
                        min_range_ratio=0.1
                    )
                    if not last_index[1]:
                        stop_word_set = stop_words_set_2 & set(vtt_word_dict.keys())
                        last_index = find_split_vtt_word(
                            total_length=text_len,
                            stop_word_set=stop_word_set,
                            vtt_word_dict=vtt_word_dict,
                            min_range_ratio=0.1
                        )

                    if 0 < last_index[1] < text_limit:
                        vtt_words_index.append(vtt_words_index[-1] + last_index[0])
                        last_end = events[i].end
                        events[i].end = self.vtt_words[vtt_words_index[-1]].start
                        events.insert(
                            i + 1,
                            pysubs2.SSAEvent(start=events[i].end,
                                             end=last_end))
                        i = i + 1
                        events_len = events_len + 1
                        text_len = text_len - last_index[1]
                j = j + 1
            else:
                if text_len:
                    # if events[i].is_comment:
                    #     # trim the empty region
                    #     cur_speed = text_len * 1000 // events[i].duration
                    #     if last_len:
                    #         last_speed = last_len * 1000 // events[i - 1].duration
                    #     else:
                    #         last_speed = 10
                    #     if cur_speed < (last_speed >> 2):
                    #         events[i].duration = last_speed * events[i].duration // 1000
                    #     events[i].is_comment = False
                    # last_len = text_len
                    text_len = 0
                    if j - vtt_words_index[-1] > 1:
                        if self.vtt_words[j - 1].speed < 10:
                            # if the duration is too big
                            # it means the start time is not accurate
                            j = j - 1
                            self.vtt_words[j - 1].end = events[i].end
                    vtt_words_index.append(j)
                    is_started = False
                    i = i + 1
                else:
                    del events[i]

        vtt_words_index = vtt_words_index[1:]
        if j == vtt_words_len:
            vtt_words_index.append(j)
            events = events[:len(vtt_words_index)]
            self.vtt_words_index = vtt_words_index
            return events
        return None


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
        style_name='Default',
        same_event_type=0, ):
    """
    Serialize a list of subtitles using pysubs2.
    """
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
                if style_name:
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.is_comment = src_ssafile.events[i].is_comment
                        event.text = text_list[i]
                        event.style = style_name
                        dst_ssafile.events.append(event)
                        i = i + 1
                else:
                    while i < length:
                        event = pysubs2.SSAEvent()
                        event.start = src_ssafile.events[i].start
                        event.end = src_ssafile.events[i].end
                        event.is_comment = src_ssafile.events[i].is_comment
                        event.text = text_list[i]
                        event.style = src_ssafile.events[i].style
                        dst_ssafile.events.append(event)
                        i = i + 1
            elif same_event_type == 1:
                # add text_list to src_ssafile
                # before the existing text in event
                if not style_name or src_ssafile.events[0].style == style_name:
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
                if not style_name or src_ssafile.events[0].style == style_name:
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
        if not style_name:
            style_name = 'Default'
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
        text_list=subtitles)
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


def split_dst_lf_src_assfile(  # pylint: disable=too-many-locals, too-many-branches
        subtitles,
        order=1,
        style_name=None):
    """
    Split bilingual subtitles file's events automatically.
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

    new_ssafile = pysubs2.SSAFile()
    new_ssafile.styles = subtitles.styles
    new_ssafile.info = subtitles.info

    new_events_1 = []
    new_events_2 = []

    if len(style_name) == 1:
        style_name = [style_name[0], style_name[0]]
    elif not style_name:
        style_name = [events_1[0].style, events_1[0].style]

    for event in events_1:
        new_text_list = event.text.split(r'\N')
        new_events_1.append(copy.deepcopy(event))
        if len(new_text_list) == 2:
            new_events_1[-1].text = new_text_list[0]
            styles = re.compile(r"{\\r(.*?)}").findall(new_text_list[1])
            new_events_1[-1].style = style_name[0]
            new_events_2.append(copy.deepcopy(event))
            if styles:
                styles = styles[0].split("\\")
                if len(styles) > 1:
                    new_events_2[-1].text = "{\\" + new_text_list[1][4 + len(styles[0]):]
                else:
                    new_events_2[-1].text = new_text_list[1][4 + len(styles[0]):]
                new_events_2[-1].style = styles[0]
            else:
                new_events_2[-1].text = new_text_list[1]
                new_events_2[-1].style = style_name[1]

    if order:
        new_events = new_events_1 + new_events_2
    else:
        new_events = new_events_2 + new_events_1

    sorted_events_list.append(new_events)

    for events in sorted_events_list:
        new_ssafile.events = new_ssafile.events + events

    return new_ssafile


def merge_bilingual_assfile(
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        subtitles,
        order=1):
    """
    Merge bilingual subtitles file's events automatically.
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
        # pylint: disable=too-many-statements, too-many-branches, too-many-arguments
        # pylint: disable=too-many-boolean-expressions
        subtitles,
        stop_words_set_1,
        stop_words_set_2,
        max_join_size=constants.DEFAULT_MAX_SIZE_PER_EVENT,
        max_delta_time=int(constants.DEFAULT_CONTINUOUS_SILENCE * 1000),
        delimiters=constants.DEFAULT_EVENT_DELIMITERS,
        avoid_split=False):
    """
    Merge a source subtitles file's events automatically.
    """
    new_ssafile = pysubs2.SSAFile()
    new_ssafile.styles = subtitles.styles
    new_ssafile.info = subtitles.info
    style_events = {}

    for event in subtitles.events:
        event.text = event.text.replace("\\N", " ")
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
    event_count = 1
    merge_count = 0
    split_count = 0

    new_ssafile.events.append(temp_ssafile.events[0])

    while event_count < sub_length:
        if not new_ssafile.events[-1].is_comment \
                and not temp_ssafile.events[event_count].is_comment \
                and new_ssafile.events[-1].style == temp_ssafile.events[event_count].style \
                and temp_ssafile.events[event_count].start \
                - new_ssafile.events[-1].end < max_delta_time \
                and new_ssafile.events[-1].text.rstrip(" ")[-1] not in delimiters \
                and temp_ssafile.events[event_count].text.lstrip(" ")[0] not in delimiters:
            if len(new_ssafile.events[-1].text) + \
                    len(temp_ssafile.events[event_count].text) < max_join_size:
                new_ssafile.events[-1].end = temp_ssafile.events[event_count].end
                if new_ssafile.events[-1].text[-1] != " ":
                    new_ssafile.events[-1].text = new_ssafile.events[-1].text + " " + \
                                                  temp_ssafile.events[event_count].text
                else:
                    new_ssafile.events[-1].text = \
                        new_ssafile.events[-1].text + temp_ssafile.events[event_count].text
                merge_count = merge_count + 1
                event_count = event_count + 1
                continue

            if not avoid_split:
                if len(new_ssafile.events[-1].text) \
                        > len(temp_ssafile.events[event_count].text) * 1.4 and \
                        len(new_ssafile.events[-1].text) > max_join_size * 0.8:
                    joint_event = new_ssafile.events[-1]
                else:
                    joint_event = join_event(new_ssafile.events[-1],
                                             temp_ssafile.events[event_count])
                event_list = []
                while True:
                    word_dict = get_slice_pos_dict(joint_event.text, delimiters=delimiters)
                    total_length = len(joint_event.text)
                    # use punctuations to split the sentence first
                    stop_word_set = set(word_dict.keys())
                    last_index = find_split_index(
                        total_length=total_length,
                        stop_word_set=stop_word_set,
                        word_dict=word_dict,
                        min_range_ratio=0.1
                    )

                    if len(word_dict) < 2 or not last_index:
                        # then use stop words
                        word_dict = get_slice_pos_dict(joint_event.text)
                        stop_word_set = stop_words_set_1 & \
                                        set(word_dict.keys())
                        last_index = find_split_index(
                            total_length=total_length,
                            stop_word_set=stop_word_set,
                            word_dict=word_dict,
                            min_range_ratio=0.1
                        )
                        if not last_index:
                            stop_word_set = stop_words_set_2 & \
                                            set(word_dict.keys())
                            last_index = find_split_index(
                                total_length=total_length,
                                stop_word_set=stop_word_set,
                                word_dict=word_dict,
                                min_range_ratio=0.1
                            )

                    if 0 < last_index < max_join_size:
                        if total_length - last_index < max_join_size:
                            event_list.extend(split_event(joint_event, last_index))
                            if joint_event.text in new_ssafile.events[-1].text:
                                last_index = -2
                            else:
                                last_index = -1
                            new_ssafile.events.pop()
                            if len(event_list) > 2:
                                count = 0
                                while count < len(event_list) - 1:
                                    joint_event = join_event(
                                        event_list[count],
                                        event_list[count + 1])
                                    if len(joint_event.text) < max_join_size:
                                        del event_list[count + 1]
                                        event_list[count] = joint_event
                                        merge_count = merge_count + 1
                                    count = count + 1
                            new_ssafile.events.extend(event_list)
                            split_count = split_count + len(event_list)
                            break
                        split_events = split_event(joint_event, last_index)
                        event_list.append(split_events[0])
                        joint_event = split_events[1]
                    else:
                        break

                if last_index < 0:
                    if last_index > -2:
                        event_count = event_count + 1
                    continue

        new_ssafile.events.append(temp_ssafile.events[event_count])
        event_count = event_count + 1

    for events in sorted_events_list:
        new_ssafile.events = events + new_ssafile.events

    print(_("Merge {count} times.").format(count=merge_count))
    print(_("Split {count} times.").format(count=split_count))
    delta = len(subtitles.events) - len(new_ssafile.events)
    if delta > 0:
        print(_("Reduce {count} lines of events.").format(count=delta))
    else:
        print(_("Add {count} lines of events.").format(count=-delta))

    return new_ssafile


def find_split_index(
        total_length,
        stop_word_set,
        word_dict,
        min_range_ratio
):
    """
    Find index to split.
    """
    half_pos = int(total_length / 2)
    min_range = int(min_range_ratio * total_length)
    max_range = total_length - min_range
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

    return last_index


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
                slice_ = sentence[j:i].lstrip(" ")
                index = result_dict.get(slice_)
                if not index:
                    result_dict[slice_] = [j]
                else:
                    result_dict[slice_].append(j)
            j = i + 1
        i = i + 1

    if i != j and sentence[j:i].strip(" "):
        slice_ = sentence[j:i].lstrip(" ")
        index = result_dict.get(slice_)
        if not index:
            result_dict[slice_] = [j]
        else:
            result_dict[slice_].append(j)

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
        position,
        without_mark=False
):
    """
    Split an event based on position.
    """
    ratio = position / len(event.text)
    first_event = event.copy()
    first_event.start = event.start
    first_event.end = int((event.end - event.start) * ratio) + event.start

    second_event = event.copy()
    second_event.end = event.end
    second_event.start = first_event.end
    if not without_mark:
        if not first_event.text.startswith("{\\r}"):
            first_event.text = "{\\r}" + event.text[:position].rstrip(" ")
        else:
            first_event.text = event.text[:position].rstrip(" ")
        if not second_event.text.startswith("{\\r}"):
            second_event.text = "{\\r}" + event.text[position:].lstrip(" ")
        else:
            second_event.text = event.text[position:].lstrip(" ")

    return [first_event, second_event]
