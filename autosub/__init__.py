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
from autosub import core
from autosub import ffmpeg_utils
from autosub import metadata
from autosub import sub_utils


class PrintAndStopException(Exception):
    """
    Raised when something need to print
    and works need to be stopped in main().
    """

    def __init__(self, msg):
        super(PrintAndStopException, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


def get_cmd_args():
    """
    Get command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog=metadata.NAME,
        usage='\n  %(prog)s <source_path> [options]',
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
    input_group = parser.add_argument_group(
        'Input Options',
        'Args to control extra input.')
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
        help="The path to the video or audio file needs to generate subtitles. "
             "If Speech Options not given, it will only generate the times."
             "(arg_num = 1)"
    )

    speech_group.add_argument(
        '-gsv2', '--gspeechv2',
        metavar='key',
        help="The Google Speech V2 API key to be used. "
             "If not provided, use free api key instead."
             "(arg_num = 1)"
    )

    speech_group.add_argument(
        '-S', '--src-language',
        metavar='locale',
        help="Locale of language spoken in source file. "
             "(arg_num = 1) (default: %(default)s)"
    )

    speech_group.add_argument(
        '-mnc', '--min-confidence',
        metavar='float',
        type=float,
        default=0.0,
        help="GoogleSpeechV2 API response for text confidence. "
             "A float value between 0 and 1. "
             "Confidence bigger means the result is better. "
             "Input this argument will drop any result below it. "
             "Ref: https://github.com/BingLingGroup/google-speech-v2#response "
             "(arg_num = 1) (default: %(default)s)"
    )

    speech_group.add_argument(
        '-sc', '--speech-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent speech-to-text API requests to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-D', '--dst-language',
        metavar='locale',
        help="Locale of desired language for the subtitles."
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-gtv2', '--gtransv2',
        metavar='key',
        help="The Google Translate V2 API key to be used. "
             "If not provided, use free api instead."
             "(arg_num = 1)"
    )

    trans_group.add_argument(
        '-lpt', '--lines-per-trans',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_LINES_PER_TRANS,
        help="Number of lines per Google Translate V2 request. "
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-slp', '--sleep-seconds',
        metavar='second',
        type=int,
        default=constants.DEFAULT_SLEEP_SECONDS,
        help="Seconds to sleep between two translation requests. "
             "(arg_num = 1) (default: %(default)s)"
    )

    trans_group.add_argument(
        '-tc', '--trans-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent "
             "Google translation V2 API requests to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    options_group.add_argument(
        '-htp', '--http-speech-to-text-api',
        action='store_true',
        help="Change the GoogleV2(speech and translation) api "
             "url into the http one. "
             "(arg_num = 0)"
    )

    output_group.add_argument(
        '-o', '--output',
        metavar='path',
        help="""The output path for subtitles file.
                (default: the source_path combined 
                with the proper name tails) (arg_num = 1)"""
    )

    output_group.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Avoid any pause and overwriting files. "
             "Stop the program when your args are wrong. (arg_num = 0)"
    )

    output_group.add_argument(
        '-of', '--output-files',
        metavar='mode',
        nargs='*',
        default="dst",
        help="Output more files. "
             "Available modes: "
             "regions, src, dst, bilingual, all "
             "(4 ≥ arg_num ≥ 1 ) (default: %(default)s)"
    )

    output_group.add_argument(
        '-F', '--format',
        metavar='format',
        default=constants.DEFAULT_SUBTITLES_FORMAT,
        help="Destination subtitles format. "
             "(arg_num = 1) (default: %(default)s)"
    )

    output_group.add_argument(
        '-fps', '--sub-fps',
        metavar='float',
        type=float,
        help="Valid when your output format is sub. "
             "If input, it will override the fps check "
             "on the input file. "
             "Ref: https://pysubs2.readthedocs.io/en/latest/api-reference.html"
             "#supported-input-output-formats"
             "(arg_num = 1)"
    )

    output_group.add_argument(
        '-der', '--drop-empty-regions',
        action='store_true',
        help="Drop any regions without text. "
             "(arg_num = 0)"
    )

    input_group.add_argument(
        '-sty', '--ass-styles',
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

    input_group.add_argument(
        '-esr', '--external-speech-regions',
        nargs='?', metavar='path',
        help="""Path to the subtitles file
                 which provides external speech regions,
                 which is one of the formats that pysubs2 supports
                 and overrides the auditok method to find speech regions.
                 (arg_num = 0 or 1)"""
    )

    # input_group.add_argument(
    #     '-esr', '--external-speech-regions',
    #     nargs='?', metavar='path',
    #     help="""Path to the subtitles file
    #                  which provides external speech regions,
    #                  which is one of the formats that pysubs2 supports
    #                  and overrides the auditok method to find speech regions.
    #                  (arg_num = 0 or 1)"""
    # )

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
        default=constants.DEFAULT_CONTINUOUS_SILENCE,
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


def list_args(args):
    """
    Check if there's any list args.
    """
    if args.list_formats:
        print("List of formats:")
        for subtitles_format, format_description in sorted(constants.FORMATTERS.items()):
            print("{sf}\t{fd}".format(sf=subtitles_format, fd=format_description))
        return True

    if args.list_speech_to_text_codes:
        print("List of all source language codes:")
        for code, language in sorted(constants.SPEECH_TO_TEXT_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return True

    if args.list_translation_codes:
        print("List of all destination language codes:")
        for code, language in sorted(constants.TRANSLATION_LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return True

    return False


def validate_args(args):  # pylint: disable=too-many-branches,too-many-return-statements, too-many-statements
    """
    Check that the commandline arguments passed to autosub are valid.
    """
    if not args.source_path or not os.path.isfile(args.source_path):
        print("Error: You need to specify a valid source path.")
        return False

    if isinstance(args.output_files, str):
        args.output_files = {args.output_files}
    else:
        args.output_files = set(args.output_files)

    if len(args.output_files) > 4:
        print(
            "Error: Too much \"-of\"/\"--output-files\" arguments."
        )
        return False
    else:
        if "all" in args.output_files:
            args.output_files = constants.DEFAULT_MODE_SET
        else:
            args.output_files = args.output_files & \
                                constants.DEFAULT_MODE_SET
            if not args.output_files:
                print(
                    "Error: No valid \"-of\"/\"--output-files\" arguments."
                )
                return False

    if args.format not in constants.FORMATTERS.keys():
        print(
            "Error: Subtitle format not supported. "
            "Run with \"-lf\"/\"--list-formats\" to see all supported formats.\n"
            "Or use ffmpeg or SubtitleEdit to convert the formats."
        )
        return False

    if args.sleep_seconds < 0 or args.lines_per_trans < 0:
        print(
            "Error: Argument's value illegal. "
        )
        return False

    if args.src_language:
        if args.src_language not in constants.SPEECH_TO_TEXT_LANGUAGE_CODES.keys():
            print(
                "Error: Source language not supported. "
                "Run with \"-lsc\"/\"--list-speech-to-text-codes\" "
                "to see all supported languages."
            )
            return False

        if args.dst_language is None:
            print(
                "Destination language not provided. "
                "Only performing speech recognition."
            )

        else:
            if args.min_confidence < 0.0 or args.min_confidence > 1.0:
                print(
                    "Error: min_confidence's value isn't legal."
                )
                return False

            if args.dst_language and \
                    args.dst_language not in constants.TRANSLATION_LANGUAGE_CODES.keys():
                print(
                    "Error: Destination language not supported. "
                    "Run with \"-ltc\"/\"--list-translation-codes\" "
                    "to see all supported languages."
                )
                return False

        if args.dst_language == args.src_language:
            print(
                "Source language is the same as the Destination language. "
                "Only performing speech recognition."
            )
            args.dst_language = None

    else:
        if args.format == 'txt':
            print(
                "Plain text don't include times. "
                "No works done."
            )
            return False

        if args.external_speech_regions:
            print(
                "You've already input times. "
                "No works done."
            )
            return False

        else:
            print(
                "Source language not provided. "
                "Only performing speech regions detection."
            )

    if not args.ass_styles:
        # when args.ass_styles is used but without option
        # its value is ' '
        if not args.external_speech_regions:
            print(
                "Error: External speech regions file not provided."
            )
            return False
        else:
            args.ass_styles = args.external_speech_regions
    else:
        # then set it to None
        args.ass_styles = None

    return True


def fix_args(args):
    """
    Check that the commandline arguments value passed to autosub are proper.
    """
    if not args.external_speech_regions:
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
                                              dmxcs=constants.DEFAULT_CONTINUOUS_SILENCE)
            )
            args.max_continuous_silence = constants.DEFAULT_CONTINUOUS_SILENCE

    if not args.output:
        args.output = os.path.splitext(args.source_path)[0]

    elif os.path.isdir(args.output):
        args.source_path = args.source_path.replace("\\", "/")
        args.output = args.output.replace("\\", "/")
        args.output = args.output.rstrip('/') + \
            '/' + os.path.basename(args.source_path).rstrip(os.path.splitext(args.source_path)[-1])
        print("Your output is a directory not a file path. "
              "Now file path set to {new}".format(new=args.output))
    else:
        args.output = os.path.splitext(args.output)[0]


def get_timed_text(
        is_empty_dropped,
        regions,
        text_list
):
    """
    Get timed text list.
    """
    if is_empty_dropped:
        # drop empty regions
        timed_text = [(region, text) for region, text in zip(regions, text_list) if text]
    else:
        # keep empty regions
        timed_text = []
        i = 0
        for region in regions:
            timed_text.append((region, text_list[i]))
            i = i + 1

    return timed_text


def main():  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    """
    Run autosub as a command-line program.
    """

    args = get_cmd_args()

    if list_args(args):
        return 0

    if not validate_args(args):
        return 1

    fix_args(args)

    if not args.yes:
        try:
            input_m = raw_input
        except NameError:
            input_m = input
    else:
        input_m = None

    if args.http_speech_to_text_api:
        gsv2_api_url = "http://" + constants.GOOGLE_SPEECH_V2_API_URL
    else:
        gsv2_api_url = "https://" + constants.GOOGLE_SPEECH_V2_API_URL
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

        if not args.output_files:
            raise PrintAndStopException(
                "\nNo works done."
                " Check your \"-of\"/\"--output-files\" option."
            )

        if args.external_speech_regions:
            # use external speech regions
            print("Using external speech regions.")
            regions = sub_utils.sub_to_speech_regions(
                source_file=args.source_path,
                sub_file=args.external_speech_regions
            )

        else:
            # use auditok_gen_speech_regions
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
                max_continuous_silence=constants.DEFAULT_CONTINUOUS_SILENCE,
                mode=mode
            )

        if args.src_language:
            # process output first
            try:
                args.output_files.remove("regions")
                times_string, extension = core.times_to_sub_str(
                    times=regions,
                    fps=fps,
                    subtitles_file_format=args.format,
                    ass_styles_file=args.ass_styles
                )
                # times to subtitles string
                times_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                              nt="times",
                                                              extension=args.format)
                subtitles_file_path = core.str_to_file(
                    str_=times_string,
                    output=times_name,
                    extension=extension,
                    input_m=input_m
                )
                # subtitles string to file

                print("Times file created at \"{}\"".format(subtitles_file_path))

                if not args.output_files:
                    raise PrintAndStopException("\nAll works done.")

            except KeyError:
                pass

            # speech to text
            text_list = core.speech_to_text(
                source_file=args.source_path,
                api_url=gsv2_api_url,
                regions=regions,
                api_key=args.gspeechv2,
                concurrency=args.speech_concurrency,
                src_language=args.src_language,
                min_confidence=args.min_confidence
            )

            if args.dst_language:
                # process output first
                try:
                    args.output_files.remove("src")
                    timed_text = get_timed_text(
                        is_empty_dropped=args.drop_empty_regions,
                        regions=regions,
                        text_list=text_list
                    )
                    src_string, extension = core.list_to_sub_str(
                        timed_subtitles=timed_text,
                        fps=fps,
                        subtitles_file_format=args.format,
                        ass_styles_file=args.ass_styles
                    )
                    # formatting timed_text to subtitles string
                    src_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                                nt=args.src_language,
                                                                extension=args.format)
                    subtitles_file_path = core.str_to_file(
                        str_=src_string,
                        output=src_name,
                        extension=extension,
                        input_m=input_m
                    )
                    # subtitles string to file
                    print("Source language subtitles "
                          "file created at \"{}\"".format(subtitles_file_path))

                    if not args.output_files:
                        raise PrintAndStopException("\nAll works done.")

                except KeyError:
                    pass

                # text translation
                if args.gtransv2:
                    # use gtransv2
                    translated_text = core.list_to_gtv2(
                        text_list=text_list,
                        api_key=args.gtransv2,
                        concurrency=args.trans_concurrency,
                        src_language=args.src_language,
                        dst_language=args.dst_language,
                        lines_per_trans=args.lines_per_trans
                    )
                else:
                    # use googletrans
                    translated_text = core.list_to_googletrans(
                        text_list,
                        src_language=args.src_language,
                        dst_language=args.dst_language,
                        sleep_seconds=args.sleep_seconds
                    )

                try:
                    args.output_files.remove("bilingual")
                    bilingual_text = text_list + translated_text
                    bilingual_regions = regions + regions
                    timed_bilingual = get_timed_text(
                        is_empty_dropped=args.drop_empty_regions,
                        regions=bilingual_regions,
                        text_list=bilingual_text
                    )
                    subtitles_string, extension = core.list_to_sub_str(
                        timed_subtitles=timed_bilingual,
                        fps=fps,
                        subtitles_file_format=args.format,
                        ass_styles_file=args.ass_styles
                    )
                    # formatting timed_text to subtitles string
                    bilingual_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                                      nt=args.src_language +
                                                                      '&' + args.dst_language,
                                                                      extension=args.format)
                    subtitles_file_path = core.str_to_file(
                        str_=subtitles_string,
                        output=bilingual_name,
                        extension=extension,
                        input_m=input_m
                    )
                    # subtitles string to file
                    print("Bilingual subtitles file "
                          "created at \"{}\"".format(subtitles_file_path))

                    if not args.output_files:
                        raise PrintAndStopException("\nAll works done.")

                except KeyError:
                    pass

                try:
                    args.output_files.remove("dst")
                    timed_text = get_timed_text(
                        is_empty_dropped=args.drop_empty_regions,
                        regions=regions,
                        text_list=translated_text
                    )

                    subtitles_string, extension = core.list_to_sub_str(
                        timed_subtitles=timed_text,
                        fps=fps,
                        subtitles_file_format=args.format,
                        ass_styles_file=args.ass_styles
                    )
                    # formatting timed_text to subtitles string
                    dst_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                                nt=args.dst_language,
                                                                extension=args.format)
                    subtitles_file_path = core.str_to_file(
                        str_=subtitles_string,
                        output=dst_name,
                        extension=extension,
                        input_m=input_m
                    )
                    # subtitles string to file
                    print("Destination language subtitles "
                          "file created at \"{}\"".format(subtitles_file_path))

                except KeyError:
                    pass

            else:
                if len(args.output_files) > 1 or not ({"dst", "src"} & args.output_files):
                    print(
                        "Override \"-of\"/\"--output-files\" due to your args too few."
                        "\nOutput source subtitles file only."
                    )
                timed_text = get_timed_text(
                    is_empty_dropped=args.drop_empty_regions,
                    regions=regions,
                    text_list=text_list
                )
                src_string, extension = core.list_to_sub_str(
                    timed_subtitles=timed_text,
                    fps=fps,
                    subtitles_file_format=args.format,
                    ass_styles_file=args.ass_styles
                )
                # formatting timed_text to subtitles string
                src_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                            nt=args.src_language,
                                                            extension=args.format)
                subtitles_file_path = core.str_to_file(
                    str_=src_string,
                    output=src_name,
                    extension=extension,
                    input_m=input_m
                )
                # subtitles string to file
                print("Source language subtitles "
                      "file created at \"{}\"".format(subtitles_file_path))

        else:
            print(
                "Override \"-of\"/\"--output-files\" due to your args too few."
                "\nOutput regions subtitles file only."
            )
            subtitles_string, extension = core.times_to_sub_str(
                times=regions,
                fps=fps,
                subtitles_file_format=args.format,
                ass_styles_file=args.ass_styles
            )
            # times to subtitles string
            times_name = "{base}.{nt}.{extension}".format(base=args.output,
                                                          nt="times",
                                                          extension=args.format)
            subtitles_file_path = core.str_to_file(
                str_=subtitles_string,
                output=times_name,
                extension=extension,
                input_m=input_m
            )
            # subtitles string to file

            print("Times file created at \"{}\"".format(subtitles_file_path))

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Works stopped.")
        return 1
    except pysubs2.exceptions.Pysubs2Error:
        print("\nError: pysubs2.exceptions. Check your file format.")
        return 1
    except PrintAndStopException as err_msg:
        print(err_msg)
        return 0

    print("\nAll works done.")
    return 0
