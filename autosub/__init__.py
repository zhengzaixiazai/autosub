#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's commandline entry point functionality.
"""
# Import built-in modules
from __future__ import absolute_import, print_function, unicode_literals
import os
import gettext
import sys
import shlex

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

    is_pause = False

    try:
        input_main = raw_input
    except NameError:
        input_main = input

    option_parser = options.get_cmd_parser()
    if len(sys.argv) > 1:
        args = option_parser.parse_args()
    else:
        option_parser.print_help()
        new_argv = input_main(_("\nInput args(without \"autosub\"): "))
        args = option_parser.parse_args(shlex.split(new_argv))
        is_pause = True

    if args.https_proxy:
        os.environ['https_proxy'] = args.https_proxy

    if args.http_proxy:
        os.environ['http_proxy'] = args.http_proxy

    if args.proxy_username:
        os.environ['proxy_username'] = args.proxy_username

    if args.proxy_password:
        os.environ['proxy_password'] = args.proxy_password

    try:
        if args.speech_config:
            cmdline_utils.validate_config_args(args)

        if cmdline_utils.list_args(args):
            raise exceptions.AutosubException(_("\nAll works done."))

        if not args.yes:
            input_m = input_main
        else:
            input_m = None

        styles_list = []
        validate_result = cmdline_utils.validate_io(args, styles_list)

        if validate_result == 0:
            if not constants.FFMPEG_CMD:
                raise exceptions.AutosubException(
                    _("Error: Dependency ffmpeg"
                      " not found on this machine."))
            if not constants.FFPROBE_CMD:
                raise exceptions.AutosubException(
                    _("Error: Dependency ffprobe"
                      " not found on this machine."))

            cmdline_utils.fix_args(args)

            if args.audio_process:
                args.audio_process = {k.lower() for k in args.audio_process}
                args.audio_process = \
                    args.audio_process & constants.DEFAULT_AUDIO_PRCS_MODE_SET
                if not args.audio_process:
                    raise exceptions.AutosubException(
                        _("Error: The args of \"-ap\"/\"--audio-process\" are wrong."
                          "\nNo works done."))
                if 'o' in args.audio_process:
                    args.keep = True
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        output_name=args.output,
                        input_m=input_m)
                    if not prcs_file:
                        raise exceptions.AutosubException(
                            _("No works done."))

                    args.input = prcs_file
                    raise exceptions.AutosubException(
                        _("Audio pre-processing complete.\nAll works done."))

                if 's' in args.audio_process:
                    args.keep = True

                if 'y' in args.audio_process:
                    prcs_file = ffmpeg_utils.audio_pre_prcs(
                        filename=args.input,
                        is_keep=args.keep,
                        cmds=args.audio_process_cmd,
                        output_name=args.output,
                        input_m=input_m)
                    args.audio_split_cmd = \
                        args.audio_split_cmd.replace(
                            "-vn -ac [channel] -ar [sample_rate] ", "")
                    if not prcs_file:
                        print(_("Audio pre-processing failed."
                                "\nUse default method."))
                    else:
                        args.input = prcs_file
                        print(_("Audio pre-processing complete."))

            else:
                args.audio_split_cmd = \
                    args.audio_split_cmd.replace(
                        "[channel]",
                        "{channel}".format(channel=args.api_audio_channel))
                args.audio_split_cmd = \
                    args.audio_split_cmd.replace(
                        "[sample_rate]",
                        "{sample_rate}".format(sample_rate=args.api_sample_rate))

                if args.api_suffix == ".ogg":
                    # regard ogg as ogg_opus
                    args.audio_split_cmd = \
                        args.audio_split_cmd.replace(
                            "-vn",
                            "-vn -c:a libopus")

            cmdline_utils.validate_aovp_args(args)
            fps = cmdline_utils.get_fps(args=args, input_m=input_m)
            cmdline_utils.audio_or_video_prcs(args,
                                              fps=fps,
                                              input_m=input_m,
                                              styles_list=styles_list)

        elif validate_result == 1:
            cmdline_utils.validate_sp_args(args)
            fps = cmdline_utils.get_fps(args=args, input_m=input_m)
            cmdline_utils.sub_trans(args,
                                    input_m=input_m,
                                    fps=fps,
                                    styles_list=None)

        raise exceptions.AutosubException(_("\nAll works done."))

    except KeyboardInterrupt:
        print(_("\nKeyboardInterrupt. Works stopped."))
    except pysubs2.exceptions.Pysubs2Error:
        print(_("\nError: pysubs2.exceptions. Check your file format."))
    except exceptions.AutosubException as err_msg:
        print(err_msg)

    if is_pause:
        input_main(_("Press Enter to exit..."))
    return 0
