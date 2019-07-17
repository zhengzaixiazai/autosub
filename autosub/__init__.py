#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's commandline entry point functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import core
from autosub import ffmpeg_utils
from autosub import cmdline_utils


def main():  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    """
    Run autosub as a command-line program.
    """

    args = cmdline_utils.get_cmd_args()

    try:
        ffmpeg_cmd = ffmpeg_utils.check_cmd("ffmpeg")
        if not ffmpeg_cmd:
            raise core.PrintAndStopException(
                "Error: Dependency ffmpeg on this machine."
            )

        if cmdline_utils.list_args(args):
            raise core.PrintAndStopException("\nAll works done.")

        if not args.yes:
            try:
                input_m = raw_input
            except NameError:
                input_m = input
        else:
            input_m = None

        styles_list = []
        if cmdline_utils.validate_io(args, styles_list) == 0:
            cmdline_utils.validate_aovp_args(args)
            cmdline_utils.fix_args(args)
            cmdline_utils.audio_or_video_prcs(args,
                                              input_m=input_m,
                                              styles_list=styles_list)

        elif cmdline_utils.validate_io(args, styles_list) == 1:
            cmdline_utils.validate_sp_args(args)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Works stopped.")
        return 1
    except pysubs2.exceptions.Pysubs2Error:
        print("\nError: pysubs2.exceptions. Check your file format.")
        return 1
    except core.PrintAndStopException as err_msg:
        print(err_msg)
        return 0

    print("\nAll works done.")
    return 0
