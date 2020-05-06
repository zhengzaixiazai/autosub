#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines ffmpeg command line calling functionality.
"""
# Import built-in modules
import subprocess
import tempfile
import re
import os
import sys
import gettext

# Import third-party modules


# Any changes to the path and your own modules
from autosub import constants
from autosub import exceptions

FFMPEG_UTILS_TEXT = gettext.translation(domain=__name__,
                                        localedir=constants.LOCALE_PATH,
                                        languages=[constants.CURRENT_LOCALE],
                                        fallback=True)

_ = FFMPEG_UTILS_TEXT.gettext


class SplitIntoAudioPiece:  # pylint: disable=too-few-public-methods
    """
    Class for converting a region of an input audio or video file into a short-term audio file
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            source_path,
            output,
            is_keep,
            cmd,
            suffix,
            include_before=0.25,
            include_after=0.25):
        self.source_path = source_path
        self.cmd = cmd
        self.suffix = suffix
        self.is_keep = is_keep
        if is_keep:
            self.include_before = 0.0
            self.include_after = 0.0
        else:
            self.include_before = include_before
            self.include_after = include_after
        self.output = output

    def __call__(self, region):
        try:
            start_ms, end_ms = region
            start = float(start_ms) / 1000.0
            end = float(end_ms) / 1000.0
            if start > self.include_before:
                start = start - self.include_before
            end += self.include_after
            if not self.is_keep or not self.output:
                temp = tempfile.NamedTemporaryFile(suffix=self.suffix, delete=False)
                command = self.cmd.format(start=start,
                                          dura=end - start,
                                          in_=self.source_path,
                                          out_=temp.name)
                prcs = subprocess.Popen(constants.cmd_conversion(command),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                prcs.communicate()
                return temp.name

            filename = self.output \
                + "-{start:0>8.3f}-{end:0>8.3f}{suffix}".format(
                    start=start,
                    end=end,
                    suffix=self.suffix)
            command = self.cmd.format(start=start,
                                      dura=end - start,
                                      in_=self.source_path,
                                      out_=filename)
            prcs = subprocess.Popen(constants.cmd_conversion(command),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            err = prcs.communicate()[1]
            if err:
                return None
            audio_file = open(filename, mode="rb")
            audio_data = audio_file.read()
            audio_file.close()
            if len(audio_data) <= 4:
                return None
            return filename

        except KeyboardInterrupt:
            return None

        except subprocess.CalledProcessError:
            raise exceptions.AutosubException(
                _("Error: ffmpeg can't split your file. "
                  "Check your audio processing options."))


def ffprobe_get_fps(  # pylint: disable=superfluous-parens
        video_file,
        input_m=input):
    """
    Return video_file's fps.
    """
    try:
        command = constants.DEFAULT_VIDEO_FPS_CMD.format(in_=video_file)
        print(command)
        prcs = subprocess.Popen(constants.cmd_conversion(command),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = prcs.communicate()
        if out:
            ffprobe_str = out.decode(sys.stdout.encoding)
            print(ffprobe_str)
        else:
            ffprobe_str = err.decode(sys.stdout.encoding)
            print(ffprobe_str)
        num_list = map(int, re.findall(r'\d+', ffprobe_str.decode(sys.stdout.encoding)))
        num_list = list(num_list)
        if len(num_list) == 2:
            fps = float(num_list[0]) / float(num_list[1])
        else:
            raise ValueError

    except (subprocess.CalledProcessError, ValueError):
        print(_("ffprobe can't get video fps.\n"
                "It is necessary when output is \".sub\"."))
        if input_m:
            input_str = input_m(_("Input your video fps. "
                                  "Any illegal input will regard as \".srt\" instead.\n"))
            try:
                fps = float(input_str)
                if fps <= 0.0:
                    raise ValueError
            except ValueError:
                print(_("Use \".srt\" instead."))
                fps = 0.0
        else:
            return 0.0

    return fps


def ffprobe_check_file(filename):
    """
    Give an audio or video file
    and check whether it is not empty by get its bitrate.
    """
    print(_("\nUse ffprobe to check conversion result."))
    command = constants.DEFAULT_CHECK_CMD.format(in_=filename)
    print(command)
    prcs = subprocess.Popen(constants.cmd_conversion(command),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = prcs.communicate()
    if out:
        ffprobe_str = out.decode(sys.stdout.encoding)
        print(ffprobe_str)
    else:
        ffprobe_str = err.decode(sys.stdout.encoding)
        print(ffprobe_str)
    bitrate_idx = ffprobe_str.find('bit_rate')
    if bitrate_idx < 0 or \
            ffprobe_str[bitrate_idx + 9:bitrate_idx + 10].lower() == 'n':
        return False
    return True


def audio_pre_prcs(  # pylint: disable=too-many-arguments, too-many-branches
        filename,
        is_keep,
        cmds,
        output_name=None,
        input_m=input):
    """
    Pre-process audio file.
    """
    output_list = [filename, ]
    if not cmds:
        cmds = constants.DEFAULT_AUDIO_PRCS_CMDS
        if not constants.FFMPEG_NORMALIZE_CMD:
            print(_("Warning: Dependency ffmpeg-normalize "
                    "not found on this machine. "
                    "Try default method."))
            return None

    if is_keep and output_name:
        for i in range(1, len(cmds) + 1):
            output_list.append(output_name
                               + '_temp_{num:0>3d}.flac'.format(num=i))

            if input_m:
                while os.path.isfile(output_list[i]):
                    print(_("There is already a file with the same name"
                            " in this location: \"{dest_name}\".").format(dest_name=output_list[i]))
                    output_list[i] = input_m(
                        _("Input a new path (including directory and file name) "
                          "for output file.\n"))
                    output_list[i] = os.path.splitext(output_list[i])[0]
                    output_list[i] = "{base}.{extension}".format(base=output_list[i],
                                                                 extension='temp.flac')
            else:
                if os.path.isfile(output_list[i]):
                    os.remove(output_list[i])

            command = cmds[i - 1].format(
                in_=output_list[i - 1],
                out_=output_list[i])
            print(command)
            subprocess.check_output(
                constants.cmd_conversion(command),
                stdin=open(os.devnull))
            if not ffprobe_check_file(output_list[i]):
                return None

    else:
        for i in range(1, len(cmds) + 1):
            temp_file = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            temp = temp_file.name
            temp_file.close()
            if os.path.isfile(temp):
                os.remove(temp)
            output_list.append(temp)
            command = cmds[i - 1].format(
                in_=output_list[i - 1],
                out_=output_list[i])
            print(command)
            subprocess.check_output(
                constants.cmd_conversion(command),
                stdin=open(os.devnull))
            if not ffprobe_check_file(output_list[i]):
                os.remove(output_list[i])
                return None
            if i > 1:
                os.remove(output_list[i - 1])

    return output_list[-1]
