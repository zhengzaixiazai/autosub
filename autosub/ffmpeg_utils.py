#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines ffmpeg command line calling functionality.
"""
# Import built-in modules
from __future__ import absolute_import, print_function, unicode_literals
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

try:
    _ = FFMPEG_UTILS_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = FFMPEG_UTILS_TEXT.gettext


class SplitIntoAudioPiece(object):  # pylint: disable=too-few-public-methods
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
        self.include_before = include_before
        self.include_after = include_after
        self.cmd = cmd
        self.suffix = suffix
        self.is_keep = is_keep
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
                subprocess.check_output(command, stdin=open(os.devnull), shell=False)
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
            subprocess.check_output(command, stdin=open(os.devnull), shell=False)
            return filename

        except KeyboardInterrupt:
            return None

        except subprocess.CalledProcessError:
            raise exceptions.AutosubException(
                _("Error: ffmpeg can't split your file. "
                  "Check your audio processing options.")
            )


def ffprobe_get_fps(  # pylint: disable=superfluous-parens
        video_file,
        input_m=input
):
    """
    Return video_file's fps.
    """
    try:
        command = constants.DEFAULT_VIDEO_FPS_CMD.format(in_=video_file)
        print(command)
        input_str = subprocess.check_output(command, stdin=open(os.devnull), shell=False)
        num_list = map(int, re.findall(r'\d+', input_str.decode(sys.stdout.encoding)))
        if len(list(num_list)) == 2:
            fps = float(num_list[0]) / float(num_list[1])
        else:
            raise ValueError

    except (subprocess.CalledProcessError, ValueError):
        print(_("ffprobe(ffmpeg) can't get video fps.\n"
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
    command = "ffprobe {in_} -show_format -pretty -loglevel quiet".format(in_=filename)
    print(command)
    ffprobe_bytes = subprocess.check_output(
        command,
        stdin=open(os.devnull),
        shell=False)
    ffprobe_str = ffprobe_bytes.decode(sys.stdout.encoding)
    bitrate_idx = ffprobe_str.find('bit_rate')
    if bitrate_idx < 0 or \
            ffprobe_str[bitrate_idx + 9:bitrate_idx + 10].lower() == 'n':
        return False
    return True


def which_exe(program_name):
    """
    Return the path for a given executable.
    """
    def is_exe(file_path):
        """
        Checks whether a file is executable.
        """
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)

    fpath = os.path.split(program_name)[0]
    if fpath:
        if is_exe(program_name):
            return program_name
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program_name)
            if is_exe(exe_file):
                return exe_file
    return None


def get_cmd(program_name):
    """
    Return the executable name. "None" returned when no executable exists.
    """
    if which_exe(program_name):
        return program_name
    if which_exe(program_name + ".exe"):
        return program_name + ".exe"
    return None


def audio_pre_prcs(  # pylint: disable=too-many-arguments
        filename,
        is_keep,
        cmds,
        output_name=None,
        input_m=input,
        ffmpeg_cmd="ffmpeg"
):
    """
    Pre-process audio file.
    """
    output_list = [filename, ]
    if not cmds:
        cmds = constants.DEFAULT_AUDIO_PRCS

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
            command = command[:7].replace('ffmpeg ', ffmpeg_cmd) + command[7:]
            print(command)
            subprocess.check_output(command, stdin=open(os.devnull), shell=False)
            if not ffprobe_check_file(output_list[i]):
                print(_("Audio pre-processing failed. Try default method."))
                return None

    else:
        temp_file = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
        temp = temp_file.name
        temp_file.close()
        if os.path.isfile(temp):
            os.remove(temp)
        output_list.append(temp)
        command = cmds[0].format(
            in_=output_list[0],
            out_=output_list[1])
        print(command)
        subprocess.check_output(command, stdin=open(os.devnull), shell=False)
        for i in range(2, len(cmds) + 1):
            temp_file = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            temp = temp_file.name
            temp_file.close()
            if os.path.isfile(temp):
                os.remove(temp)
            output_list.append(temp)
            command = cmds[i - 1].format(
                in_=output_list[i - 1],
                out_=output_list[i])
            command = command[:7].replace('ffmpeg ', ffmpeg_cmd) + command[7:]
            print(command)
            subprocess.check_output(command, stdin=open(os.devnull), shell=False)
            os.remove(output_list[i - 1])
            if not ffprobe_check_file(output_list[i]):
                print(_("Audio pre-processing failed. Try default method."))
                os.remove(output_list[i])
                return None

    return output_list[-1]
