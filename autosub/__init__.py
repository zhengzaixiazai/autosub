#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's commandline entry point functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import os

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import ffmpeg_utils
from autosub import cmdline_utils
from autosub import options
from autosub import exceptions


def main():  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    """
    Run autosub as a command-line program.
    """

    args = options.get_cmd_args()

    if args.https_proxy:
        os.environ['https_proxy'] = args.https_proxy

    if args.http_proxy:
        os.environ['http_proxy'] = args.http_proxy

    if args.proxy_username:
        os.environ['proxy_username'] = args.proxy_username

    if args.proxy_password:
        os.environ['proxy_password'] = args.proxy_password

    try:
        ffmpeg_cmd = ffmpeg_utils.get_cmd("ffmpeg")
        if not ffmpeg_cmd:
            raise exceptions.AutosubException(
                "Error: Dependency ffmpeg on this machine."
            )

        ffmpeg_cmd = ffmpeg_cmd + ' '
        if cmdline_utils.list_args(args):
            raise exceptions.AutosubException("\nAll works done.")

        if not args.yes:
            try:
                input_m = raw_input
            except NameError:
                input_m = input
        else:
            input_m = None

        styles_list = []
        validate_result = cmdline_utils.validate_io(args, styles_list)

        if validate_result == 0:
            if args.audio_process:
                if 'o' in args.audio_process:
                    args.keep = True
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        input_m=input_m,
                        ffmpeg_cmd=ffmpeg_cmd
                    )
                    if not prcs_file:
                        raise exceptions.AutosubException(
                            "No works done."
                        )
                    else:
                        args.input = prcs_file
                        raise exceptions.AutosubException(
                            "Audio pre-processing complete.\nAll works done."
                        )

                if 'y' in args.audio_process:
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        input_m=input_m,
                        ffmpeg_cmd=ffmpeg_cmd
                    )
                    if not prcs_file:
                        no_audio_prcs = False
                    else:
                        args.input = prcs_file
                        print("Audio pre-processing complete.")
                        no_audio_prcs = True
                elif 'n' in args.audio_process:
                    print("No extra check/conversion "
                          "before the speech-to-text procedure.")
                    no_audio_prcs = True
                else:
                    no_audio_prcs = False

                if 's' in args.audio_process:
                    args.keep = True

            else:
                no_audio_prcs = False

            cmdline_utils.validate_aovp_args(args)
            cmdline_utils.fix_args(args,
                                   ffmpeg_cmd=ffmpeg_cmd)
            fps = cmdline_utils.get_fps(args=args, input_m=input_m)
            cmdline_utils.audio_or_video_prcs(args,
                                              fps=fps,
                                              input_m=input_m,
                                              styles_list=styles_list,
                                              no_audio_prcs=no_audio_prcs)

        elif validate_result == 1:
            cmdline_utils.validate_sp_args(args)
            fps = cmdline_utils.get_fps(args=args, input_m=input_m)
            cmdline_utils.subs_trans(args,
                                     input_m=input_m,
                                     fps=fps,
                                     styles_list=None)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Works stopped.")
        return 1
    except pysubs2.exceptions.Pysubs2Error:
        print("\nError: pysubs2.exceptions. Check your file format.")
        return 1
    except exceptions.AutosubException as err_msg:
        print(err_msg)
        return 0

    print("\nAll works done.")
    return 0
