#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's commandline entry point functionality.
"""
# Import built-in modules
from __future__ import absolute_import, print_function, unicode_literals
import os
import gettext

# Import third-party modules
import pysubs2

# Any changes to the path and your own modules
from autosub import ffmpeg_utils
from autosub import cmdline_utils
from autosub import options
from autosub import exceptions
from autosub import constants

INIT_TEXT = gettext.translation(domain=__name__,
                                localedir=constants.LOCALE_PATH,
                                languages=[constants.CURRENT_LOCALE],
                                fallback=True)

try:
    _ = INIT_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = INIT_TEXT.gettext


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
            ffmpeg_cmd = ffmpeg_utils.get_cmd("ffmpeg")
            if not ffmpeg_cmd:
                raise exceptions.AutosubException(
                    _("Error: Dependency ffmpeg"
                      " not found on this machine.")
                )

            ffmpeg_cmd = ffmpeg_cmd + ' '
            if cmdline_utils.list_args(args):
                raise exceptions.AutosubException(_("\nAll works done."))

            if args.audio_process:
                args.audio_process = {k.lower() for k in args.audio_process}
                args.audio_process = \
                    args.audio_process & constants.DEFAULT_AUDIO_PRCS_MODE_SET
                if not args.audio_process:
                    raise exceptions.AutosubException(
                        _("Error: The args of \"-ap\"/\"--audio-process\" are wrong."
                          "\nNo works done.")
                    )
                if 'o' in args.audio_process:
                    args.keep = True
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        output_name=args.output,
                        input_m=input_m,
                        ffmpeg_cmd=ffmpeg_cmd
                    )
                    if not prcs_file:
                        raise exceptions.AutosubException(
                            _("No works done.")
                        )
                    else:
                        args.input = prcs_file
                        raise exceptions.AutosubException(
                            _("Audio pre-processing complete.\nAll works done.")
                        )

                if 's' in args.audio_process:
                    args.keep = True

                if 'y' in args.audio_process:
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        output_name=args.output,
                        input_m=input_m,
                        ffmpeg_cmd=ffmpeg_cmd
                    )
                    if not prcs_file:
                        no_audio_prcs = False
                    else:
                        args.input = prcs_file
                        print(_("Audio pre-processing complete."))
                        no_audio_prcs = True
                elif 'n' in args.audio_process:
                    print(_("No extra check/conversion "
                            "before the speech-to-text procedure."))
                    no_audio_prcs = True
                else:
                    no_audio_prcs = False

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
        print(_("\nKeyboardInterrupt. Works stopped."))
        return 1
    except pysubs2.exceptions.Pysubs2Error:
        print(_("\nError: pysubs2.exceptions. Check your file format."))
        return 1
    except exceptions.AutosubException as err_msg:
        print(err_msg)
        return 0

    print(_("\nAll works done."))
    return 0
