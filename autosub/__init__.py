#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's commandline functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import argparse
import os

# Import third-party modules
import pysubs2
import auditok

# Any changes to the path and your own modules
from autosub import constants
from autosub import metadata
from autosub import ffmpeg_utils
from autosub import core


def get_cmd_args():
    """
    Get command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog=metadata.NAME,
        usage='\n  %(prog)s source_path [options]',
        description=metadata.DESCRIPTION,
        epilog="""Make sure the argument with space is in quotes.
The default value is used 
when the option is not present at the command line.
The \"arg_num\" in the help means if the option is input,
the number of the arguments is required.\n
Author: {author}
Email: {email}
Bug report: https://github.com/agermanidis/autosub\n
""".format(author=metadata.AUTHOR, email=metadata.AUTHOR_EMAIL),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    required_group = parser.add_argument_group('Required')
    options_group = parser.add_argument_group('Options')
    speech_group = parser.add_argument_group(
        'Speech Options',
        'Args to control speech-to-text.')
    trans_group = parser.add_argument_group(
        'Translation Options',
        'Args to control translation.')
    output_group = parser.add_argument_group(
        'Output Options',
        'Args to control output.')
    auditok_group = parser.add_argument_group(
        'Auditok Options',
        'Args to control Auditok which is the '
        'default speech regions find method.')
    list_group = parser.add_argument_group(
        'List Options',
        'List all available arguments.')

    required_group.add_argument(
        'source_path',
        nargs='?', metavar='path',
        help="The path to the video or audio file needs to generate subtitle. "
             "(arg_num = 1)"
    )

    output_group.add_argument(
        '-o', '--output',
        metavar='path',
        help="""The output path for subtitle file.
                (default: the source_path combined 
                with the destination language code) (arg_num = 1)"""
    )

    output_group.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Avoid any pause and overwriting files. "
             "Stop the program when your args are wrong. (arg_num = 0)"
    )

    output_group.add_argument(
        '-F', '--format',
        metavar='format',
        default=constants.DEFAULT_SUBTITLES_FORMAT,
        help="Destination subtitle format. "
             "(arg_num = 1) (default: %(default)s)"
    )

    output_group.add_argument(
        '-fps', '--sub-fps',
        metavar='number',
        type=float,
        help="Valid when your output format is sub. "
             "If input, it will override the fps check "
             "on the input file. "
             "Ref: https://pysubs2.readthedocs.io/en/latest/api-reference.html"
             "#supported-input-output-formats"
             "(arg_num = 1)"
    )

    output_group.add_argument(
        '-aty', '--ass-styles',
        nargs='?', metavar='path',
        default=' ',
        help="""Valid when your output format is ass/ssa.
             Path to the subtitles file
             which provides ass/ssa styles for your output.
             If the arg_num is 0,
             it will use the styles from the 
             \"-esr/--external-speech-regions\".
             Currently events style only support one kind.
             (arg_num = 0 or 1)"""
    )

    speech_group.add_argument(
        '-esr', '--external-speech-regions',
        nargs='?', metavar='path',
        help="""Path to the subtitles file
             which provides external speech regions,
             which is one of the formats that pysubs2 supports
             and overrides the auditok method to find speech regions.
             (arg_num = 0 or 1)"""
    )

    speech_group.add_argument(
        '-S', '--src-language',
        metavar='locale',
        default=constants.DEFAULT_SRC_LANGUAGE,
        help="Locale of language spoken in source file. "
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-D', '--dst-language',
        metavar='locale',
        help="Locale of desired language for the subtitles."
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-K', '--api-key',
        metavar='key',
        help="The Google Translate API key to be used. "
             "Required for subtitles translation. "
             "(arg_num = 1)"
    )

    options_group.add_argument(
        '-C', '--concurrency',
        metavar='number',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent API requests to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    options_group.add_argument(
        '-htp', '--http-speech-to-text-api',
        action='store_true',
        help="Change the GoogleV2(speech and translation) api "
             "url into the http one. "
             "(arg_num = 0)"
    )

    options_group.add_argument(
        '-h', '--help',
        action='help',
        help="Show %(prog)s help message and exit. (arg_num = 0)"
    )

    options_group.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s ' + metadata.VERSION
        + ' by ' + metadata.AUTHOR + ' <'
        + metadata.AUTHOR_EMAIL + '>',
        help="Show %(prog)s version and exit. (arg_num = 0)"
    )

    auditok_group.add_argument(
        '-et', '--energy-threshold',
        metavar='energy',
        type=int,
        default=constants.DEFAULT_ENERGY_THRESHOLD,
        help="The energy level which determines the region to be detected. "
             "Ref: https://auditok.readthedocs.io/en/latest/apitutorial.html"
             "#examples-using-real-audio-data "
             "(arg_num = 1) (default: %(default)s)"
    )

    auditok_group.add_argument(
        '-mnrs', '--min-region-size',
        metavar='second',
        type=float,
        default=constants.MIN_REGION_SIZE,
        help="Minimum region size "
             "when not using external speech regions control. "
             "Same docs above. "
             "(arg_num = 1) (default: %(default)s)"
    )

    auditok_group.add_argument(
        '-mxrs', '--max-region-size',
        metavar='second',
        type=float,
        default=constants.MAX_REGION_SIZE,
        help="Maximum region size "
             "when not using external speech regions control. "
             "Same docs above. "
             "(arg_num = 1) (default: %(default)s)"
    )

    auditok_group.add_argument(
        '-mxcs', '--max-continuous-silence',
        metavar='second',
        type=float,
        default=constants.MAX_CONTINUOUS_SILENCE,
        help="Maximum length of a tolerated silence within a valid audio activity. "
             "Same docs above. "
             "(arg_num = 1) (default: %(default)s)"
    )

    auditok_group.add_argument(
        '-sml', '--strict-min-length',
        action='store_true',
        help="Ref: https://auditok.readthedocs.io/en/latest/core.html#class-summary "
             "(arg_num = 0)"
    )

    auditok_group.add_argument(
        '-dts', '--drop-trailing-silence',
        action='store_true',
        help="Ref: https://auditok.readthedocs.io/en/latest/core.html#class-summary "
             "(arg_num = 0)"
    )

    list_group.add_argument(
        '-lf', '--list-formats',
        action='store_true',
        help="""List all available output subtitles formats.
If your format is not supported,
you can use ffmpeg or SubtitleEdit to convert the formats. 
[ATTENTION]: You need to offer fps option 
             when input is an audio file
             and output is sub format.
(arg_num = 0)"""
    )

    list_group.add_argument(
        '-lsc', '--list-speech-to-text-codes',
        action='store_true',
        help="""List all available source language codes,
which mean the available speech-to-text
language codes.
[ATTENTION]: Its name is different from 
             the destination language codes.
Reference: https://cloud.google.com/speech-to-text/docs/languages
           https://tools.ietf.org/html/bcp47
(arg_num = 0)"""
    )

    list_group.add_argument(
        '-ltc', '--list-translation-codes',
        action='store_true',
        help="""List all available destination language codes,
which mean the available translation
language codes.
[ATTENTION]: Its name is different from 
           the destination language codes.
Reference: https://cloud.google.com/speech-to-text/docs/languages
           https://tools.ietf.org/html/bcp47
(arg_num = 0)"""
    )

    return parser.parse_args()


def validate(args):  # pylint: disable=too-many-branches,too-many-return-statements
    """
    Check that the CLI arguments passed to autosub are valid.
    """
    if args.list_formats:
        print("List of formats:")
        for subtitles_format, format_description in sorted(constants.FORMATTERS.items()):
            print("{sf}\t{fd}".format(sf=subtitles_format, fd=format_description))
        return False

    if args.list_speech_to_text_codes:
        print("List of all source language codes:")
        for code, language in sorted(constants.SPEECH_TO_TEXT_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return False

    if args.list_translation_codes:
        print("List of all destination language codes:")
        for code, language in sorted(constants.TRANSLATION_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return False

    if not args.source_path or not os.path.isfile(args.source_path):
        print("Error: You need to specify a valid source path.")
        return False

    if args.format not in constants.FORMATTERS.keys():
        print(
            "Error: Subtitle format not supported. "
            "Run with \"-lf\" or \"--list-formats\" to see all supported formats.\n"
            "Or use ffmpeg or SubtitleEdit to convert the formats."
        )
        return False

    if args.src_language not in constants.SPEECH_TO_TEXT_LANGUAGE_CODES.keys():
        print(
            "Error: Source language not supported. "
            "Run with \"-lsc\" or \"--list-speech-to-text-codes\" "
            "to see all supported languages."
        )
        return False

    if args.dst_language is None:
        print(
            "Destination language not provided. "
            "Only performing speech recognition."
        )
        args.dst_language = args.src_language

    elif args.dst_language == args.src_language:
        print(
            "Source language is the same as the Destination language. "
            "Only performing speech recognition."
        )

    elif args.dst_language not in constants.TRANSLATION_LANGUAGE_CODES.keys():
        print(
            "Error: Destination language not supported. "
            "Run with \"-ltc\" or \"--list-translation-codes\" "
            "to see all supported languages."
        )
        return False

    if not args.ass_styles:
        # when args.ass_styles is used but without option
        if not args.external_speech_regions:
            print(
                "Error: External speech regions file not provided."
            )
            return False
        else:
            args.ass_styles = args.external_speech_regions
    else:
        args.ass_styles = None

    if args.min_region_size < constants.MIN_REGION_SIZE:
        print(
            "Your minimum region size {mrs0} is smaller than {mrs}.\n"
            "Now reset to {mrs}".format(mrs0=args.min_region_size,
                                        mrs=constants.MIN_REGION_SIZE)
        )
        args.min_region_size = constants.MIN_REGION_SIZE

    if args.max_region_size > constants.MAX_EXT_REGION_SIZE:
        print(
            "Your maximum region size {mrs0} is larger than {mrs}.\n"
            "Now reset to {mrs}".format(mrs0=args.max_region_size,
                                        mrs=constants.MAX_EXT_REGION_SIZE)
        )
        args.max_region_size = constants.MAX_EXT_REGION_SIZE

    if args.max_continuous_silence < 0:
        print(
            "Your maximum continuous silence {mxcs} is smaller than 0.\n"
            "Now reset to {dmxcs}".format(mxcs=args.max_continuous_silence,
                                          dmxcs=constants.MAX_CONTINUOUS_SILENCE)
        )
        args.max_continuous_silence = constants.MAX_CONTINUOUS_SILENCE

    return True


def main():  # pylint: disable=too-many-branches, too-many-statements
    """
    Run autosub as a command-line program.
    """

    args = get_cmd_args()

    if not args.yes:
        try:
            input_m = raw_input
        except NameError:
            input_m = input
    else:
        input_m = None

    if not validate(args):
        return 1

    if args.http_speech_to_text_api:
        api_url = "http://" + constants.GOOGLE_SPEECH_V2_API_URL
    else:
        api_url = "https://" + constants.GOOGLE_SPEECH_V2_API_URL
    try:
        if args.format == 'sub':
            if not args.sub_fps:
                fps = ffmpeg_utils.ffprobe_get_fps(
                    args.source_path,
                    input_m=input_m)
                if fps == 0.0:
                    if not args.yes:
                        args.format = 'srt'
                    else:
                        raise pysubs2.exceptions.Pysubs2Error
            else:
                fps = args.sub_fps
        else:
            fps = 0.0

        if not args.output:
            base = os.path.splitext(args.source_path)[0]
            args.output = "{base}.{langcode}.{extension}".format(base=base,
                                                                 langcode=args.dst_language,
                                                                 extension=args.format)
        elif os.path.isdir(args.output):
            base = args.output + '.'.split(os.path.basename(args.source_path))[0]
            args.output = "{base}.{langcode}.{extension}".format(base=base,
                                                                 langcode=args.dst_language,
                                                                 extension=args.format)
            print("Your output is a directory not a file path. "
                  "Now file path set to {new}".format(new=args.output))

        if args.external_speech_regions:
            print("Using external speech regions.")
            regions = core.sub_gen_speech_regions(
                source_file=args.source_path,
                sub_file=args.external_speech_regions
            )

        else:
            mode = 0
            if args.strict_min_length:
                mode = auditok.StreamTokenizer.STRICT_MIN_LENGTH
                if args.drop_trailing_silence:
                    mode = mode | auditok.StreamTokenizer.DROP_TRAILING_SILENCE
            elif args.drop_trailing_silence:
                mode = auditok.StreamTokenizer.DROP_TRAILING_SILENCE

            regions = core.auditok_gen_speech_regions(
                source_file=args.source_path,
                energy_threshold=args.energy_threshold,
                min_region_size=constants.MIN_REGION_SIZE,
                max_region_size=constants.MAX_REGION_SIZE,
                max_continuous_silence=constants.MAX_CONTINUOUS_SILENCE,
                mode=mode
            )

        timed_subtitles = core.api_gen_text(
            source_file=args.source_path,
            api_url=api_url,
            regions=regions,
            api_key=args.api_key,
            concurrency=args.concurrency,
            src_language=args.src_language,
            dst_language=args.dst_language
        )

        subtitles_file_path = core.list_to_sub_file(
            timed_subtitles=timed_subtitles,
            output=args.output,
            fps=fps,
            subtitles_file_format=args.format,
            input_m=input_m,
            ass_styles_file=args.ass_styles
        )
        print("\nSubtitles file created at \"{}\"".format(subtitles_file_path))

    except KeyboardInterrupt:
        return 1
    except pysubs2.exceptions.Pysubs2Error:
        print("Error: pysubs2.exceptions. Check your file format.")
        return 1

    return 0
