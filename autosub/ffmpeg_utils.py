#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines ffmpeg command line calling functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import subprocess
import tempfile
import re
import os

# Import third-party modules


# Any changes to the path and your own modules


class SplitIntoFLACPiece(object):  # pylint: disable=too-few-public-methods
    """
    Class for converting a region of an input audio or video file into a FLAC audio file
    """

    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            start_ms, end_ms = region
            start = float(start_ms) / 1000.0
            end = float(end_ms) / 1000.0
            start = max(0.0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            command = ["ffmpeg", "-ss", str(start), "-t", str(end - start),
                       "-y", "-i", self.source_path, "-c", "copy",
                       "-loglevel", "error", temp.name]
            use_shell = True if os.name == "nt" else False
            subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
            read_data = temp.read()
            temp.close()
            os.unlink(temp.name)
            return read_data

        except KeyboardInterrupt:
            return None


def ffprobe_get_fps(  # pylint: disable=superfluous-parens
        video_file,
        input_m=input
):
    """
    Return video_file's fps.
    """
    try:
        command = ["ffprobe", "-v", "0", "-of", "csv=p=0",
                   "-select_streams", "v:0", "-show_entries",
                   "stream=r_frame_rate", video_file]
        use_shell = True if os.name == "nt" else False
        input_str = subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
        num_list = map(int, re.findall(r'\d+', input_str.decode('utf-8')))
        if len(list(num_list)) == 2:
            fps = float(num_list[0]) / float(num_list[1])
        else:
            raise ValueError

    except (subprocess.CalledProcessError, ValueError):
        print("ffprobe(ffmpeg) can't get video fps.\n"
              "It is necessary when output is \".sub\".")
        if input_m:
            input_str = input_m("Input your video fps. "
                                "Any illegal input will regard as \".srt\" instead.\n")
            try:
                fps = float(input_str)
                if fps <= 0.0:
                    raise ValueError
            except ValueError:
                print("Use \".srt\" instead.")
                fps = 0.0
        else:
            return 0.0

    return fps


def which_exe(program):
    """
    Return the path for a given executable.
    """
    def is_exe(file_path):
        """
        Checks whether a file is executable.
        """
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def ffmpeg_check():
    """
    Return the ffmpeg executable name. "None" returned when no executable exists.
    """
    if which_exe("ffmpeg"):
        return "ffmpeg"
    if which_exe("ffmpeg.exe"):
        return "ffmpeg.exe"
    return None


def source_to_audio(  # pylint: disable=superfluous-parens
        filename, channels=1,
        rate=48000, file_ext='.wav',
        ffmpeg_loglevel='error'):
    """
    Convert input file to a temporary audio file.
    """
    temp = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
    if not os.path.isfile(filename):
        print("The given file does not exist: {}.".format(filename))
        raise Exception("Invalid filepath: {}.".format(filename))
    if not ffmpeg_check():
        print("ffmpeg: Executable not found on this machine.")
        raise Exception("Dependency not found: ffmpeg.")
    command = [ffmpeg_check(), "-y", "-i", filename,
               "-ac", str(channels), "-ar", str(rate),
               "-loglevel", ffmpeg_loglevel, temp.name]
    use_shell = True if os.name == "nt" else False
    subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
    return temp.name
