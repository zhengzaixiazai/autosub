#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's command line options.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
import argparse

# Import third-party modules


# Any changes to the path and your own modules
from autosub import metadata
from autosub import constants


def get_cmd_args():  # pylint: disable=too-many-statements
    """
    Get command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog=metadata.NAME,
        usage='\n  %(prog)s <input> [options]',
        description=metadata.DESCRIPTION,
        epilog="""Make sure the argument with space is in quotes.
The default value is used 
when the option is not present at the command line.
\"(arg_num)\" means if the option is input,
the number of the arguments is required.\n
Author: {author}
Email: {email}
Bug report: https://github.com/agermanidis/autosub\n
""".format(author=metadata.AUTHOR, email=metadata.AUTHOR_EMAIL),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    input_group = parser.add_argument_group(
        'Input Options',
        'Args to control input.')
    lang_group = parser.add_argument_group(
        'Language Options',
        'Args to control language.')
    output_group = parser.add_argument_group(
        'Output Options',
        'Args to control output.')
    speech_group = parser.add_argument_group(
        'Speech Options',
        'Args to control speech-to-text. '
        'If Speech Options not given, it will only generate the times.')
    pygt_group = parser.add_argument_group(
        'py-googletrans Options',
        'Args to control translation. '
        'Default method to translate. '
        'Could be blocked at any time.')
    gsv2_group = parser.add_argument_group(
        'Google Speech V2 Options',
        'Args to control translation.(Not been tested) '
        'If the api key is given, '
        'it will replace the py-googletrans method.')
    options_group = parser.add_argument_group(
        'Other Options',
        'Other options to control.')
    audio_prcs_group = parser.add_argument_group(
        'Audio Processing Options',
        'Args to control audio processing.')
    auditok_group = parser.add_argument_group(
        'Auditok Options',
        'Args to control Auditok '
        'when not using external speech regions control.')
    list_group = parser.add_argument_group(
        'List Options',
        'List all available arguments.')

    input_group.add_argument(
        '-i', '--input',
        nargs='?', metavar='path',
        help="The path to the video/audio/subtitles file "
             "needs to generate subtitles. "
             "When it is a subtitles file, "
             "the program will only translate it. "
             "(arg_num = 1)"
    )

    input_group.add_argument(
        '-er', '--ext-regions',
        metavar='path',
        help="""Path to the subtitles file
                which provides external speech regions,
                which is one of the formats that pysubs2 supports
                and overrides the auditok method to find speech regions.
                (arg_num = 1)"""
    )

    input_group.add_argument(
        '-sty', '--styles',
        nargs='?', metavar='path',
        const=' ',
        help="""Valid when your output format is \"ass\"/\"ssa\".
                Path to the subtitles file
                which provides \"ass\"/\"ssa\" styles for your output.
                If the arg_num is 0,
                it will use the styles from the
                \"-esr\"/\"--external-speech-regions\".
                More info on \"-sn\"/\"--styles-name\".
                (arg_num = 0 or 1)"""
    )

    input_group.add_argument(
        '-sn', '--styles-name',
        nargs='*', metavar='style-name',
        help="""Valid when your output format is \"ass\"/\"ssa\"
                and \"-sty\"/\"--styles\" is given.
                Adds \"ass\"/\"ssa\" styles to your events.
                If not provided, events will use the first one
                from the file.
                If the arg_num is 1, events will use the 
                specific style from the arg of \"-sty\"/\"--styles\".
                If the arg_num is 2, src language events use the first.
                Dst language events use the second.               
                (arg_num = 1 or 2)"""
    )

    lang_group.add_argument(
        '-S', '--speech-language',
        metavar='lang_code',
        help="Lang code/Lang tag for speech-to-text. "
             "Recommend using the Google Cloud Speech reference "
             "lang codes. "
             "WRONG INPUT WON'T STOP RUNNING. "
             "But use it at your own risk. "
             "Ref: https://cloud.google.com/speech-to-text/docs/languages"
             "(arg_num = 1) (default: %(default)s)"
    )

    lang_group.add_argument(
        '-SRC', '--src-language',
        metavar='lang_code',
        help="Lang code/Lang tag for translation source language. "
             "If not given, use langcodes-py2 to get a best matching "
             "of the \"-S\"/\"--speech-language\". "
             "If using py-googletrans as the method to translate, "
             "WRONG INPUT STOP RUNNING. "
             "(arg_num = 1) (default: %(default)s)"
    )

    lang_group.add_argument(
        '-D', '--dst-language',
        metavar='lang_code',
        help="Lang code/Lang tag for translation destination language. "
             "Same attention in the \"-Src\"/\"--src-language\". "
             "(arg_num = 1) (default: %(default)s)"
    )

    lang_group.add_argument(
        '-bm', '--best-match',
        metavar='mode',
        nargs="*",
        help="Allow langcodes-py2 to get a best matching lang code "
             "when your input is wrong. "
             "Only functional for py-googletrans and Google Speech V2. "
             "Available modes: "
             "s, src, d, all. "
             "\"s\" for \"-S\"/\"--speech-language\". "
             "\"src\" for \"-Src\"/\"--src-language\". "
             "\"d\" for \"-D\"/\"--dst-language\". "
             "(3 ≥ arg_num ≥ 1)"
    )

    lang_group.add_argument(
        '-mns', '--min-score',
        metavar='integer',
        type=int,
        help="""An integer between 0 and 100
                to control the good match group of 
                \"-lsc\"/\"--list-speech-codes\"
                or \"-ltc\"/\"--list-translation-codes\"
                or the match result in \"-bm\"/\"--best-match\".
                Result will be a group of \"good match\"
                whose score is above this arg.
                (arg_num = 1)"""
    )

    output_group.add_argument(
        '-o', '--output',
        metavar='path',
        help="""The output path for subtitles file.
                (default: the \"input\" path combined 
                with the proper name tails) (arg_num = 1)"""
    )

    output_group.add_argument(
        '-F', '--format',
        metavar='format',
        help="Destination subtitles format. "
             "If not provided, use the extension "
             "in the \"-o\"/\"--output\" arg. "
             "If \"-o\"/\"--output\" arg doesn't provide "
             "the extension name, use \"{dft}\" instead. "
             "In this case, if \"-i\"/\"--input\" arg is a subtitles file, "
             "use the same extension from the subtitles file. "
             "(arg_num = 1) (default: {dft})".format(
                 dft=constants.DEFAULT_SUBTITLES_FORMAT)
    )

    output_group.add_argument(
        '-y', '--yes',
        action='store_true',
        help="Avoid any pause and overwriting files. "
             "Stop the program when your args are wrong. (arg_num = 0)"
    )

    output_group.add_argument(
        '-of', '--output-files',
        metavar='type',
        nargs='*',
        default=["dst", ],
        help="Output more files. "
             "Available types: "
             "regions, src, dst, bilingual, all. "
             "(4 ≥ arg_num ≥ 1) (default: %(default)s)"
    )

    output_group.add_argument(
        '-fps', '--sub-fps',
        metavar='float',
        type=float,
        help="Valid when your output format is \"sub\". "
             "If input, it will override the fps check "
             "on the input file. "
             "Ref: https://pysubs2.readthedocs.io/en/latest/api-reference.html"
             "#supported-input-output-formats "
             "(arg_num = 1)"
    )

    output_group.add_argument(
        '-der', '--drop-empty-regions',
        action='store_true',
        help="Drop any regions without text. "
             "(arg_num = 0)"
    )

    speech_group.add_argument(
        '-gsv2', '--gspeechv2',
        metavar='key',
        help="The Google Speech V2 API key to be used. "
             "If not provided, use free API key instead."
             "(arg_num = 1)"
    )

    speech_group.add_argument(
        '-mnc', '--min-confidence',
        metavar='float',
        type=float,
        default=0.0,
        help="Google Speech V2 API response for text confidence. "
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
        help="Number of concurrent Google Speech V2 requests to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    pygt_group.add_argument(
        '-slp', '--sleep-seconds',
        metavar='second',
        type=float,
        default=constants.DEFAULT_SLEEP_SECONDS,
        help="(Experimental)Seconds to sleep "
             "between two translation requests. "
             "(arg_num = 1) (default: %(default)s)"
    )

    pygt_group.add_argument(
        '-surl', '--service-urls',
        metavar='url',
        nargs='*',
        help="(Experimental)Customize request urls. "
             "Ref: https://py-googletrans.readthedocs.io/en/latest/"
             "(arg_num = 1)"
    )

    pygt_group.add_argument(
        '-ua', '--user-agent',
        metavar='User-Agent header',
        help="(Experimental)Customize User-Agent header. "
             "Same docs above. "
             "(arg_num = 1)"
    )

    gsv2_group.add_argument(
        '-gtv2', '--gtransv2',
        metavar='key',
        help="The Google Translate V2 API key to be used. "
             "If not provided, use free API(py-googletrans) instead. "
             "(arg_num = 1)"
    )

    gsv2_group.add_argument(
        '-lpt', '--lines-per-trans',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_LINES_PER_TRANS,
        help="Number of lines per Google Translate V2 request. "
             "(arg_num = 1) (default: %(default)s)"
    )

    gsv2_group.add_argument(
        '-tc', '--trans-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent "
             "Google translate V2 API requests to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    options_group.add_argument(
        '-htp', '--http-speech-to-text-api',
        action='store_true',
        help="Change the Google Speech V2 API "
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

    audio_prcs_group.add_argument(
        '-ap', '--audio-process',
        nargs='*', metavar='mode',
        default=['d', ],
        help="""Option to control audio process.
                If not given the option, 
                do normal conversion work.
                (default: %(default)s)
                \"y\": it will process the input first
                then start normal workflow.
                If succeed, no more conversion before
                the speech-to-text procedure.
                \"o\": means only process the input audio
                (\"-k\"/\"--keep\" is true).
                \"s\": means only split the input audio
                (\"-k\"/\"--keep\" is true).
                \"n\": means FORCED NO EXTRA CHECK/CONVERSION
                before the speech-to-text procedure.
                Default command to process the audio:
                {dft_1} | {dft_2} | {dft_3}
                (Ref: 
                https://github.com/stevenj/autosub/blob/master/scripts/subgen.sh
                https://ffmpeg.org/ffmpeg-filters.html)
                (2 ≥ arg_num = ≥ 1)""".format(
                    dft_1=constants.DEFAULT_AUDIO_PRCS[0],
                    dft_2=constants.DEFAULT_AUDIO_PRCS[1],
                    dft_3=constants.DEFAULT_AUDIO_PRCS[2])
    )

    audio_prcs_group.add_argument(
        '-k', '--keep',
        action='store_true',
        help="Keep audio processing files to the output path. "
             "(arg_num = 0)"
    )

    audio_prcs_group.add_argument(
        '-apc', '--audio-process-cmd',
        nargs='*', metavar='command',
        help="This arg will override the default "
             "audio process command. "
             "Every line of the commands need to be in quotes. "
             "Input file name is {in_}. "
             "Output file name is {out_}. "
             "(arg_num = 0 or 1)"
    )

    audio_prcs_group.add_argument(
        '-ac', '--audio-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help="Number of concurrent ffmpeg audio split process to make. "
             "(arg_num = 1) (default: %(default)s)"
    )

    audio_prcs_group.add_argument(
        '-acc', '--audio-conversion-cmd',
        metavar='command',
        help="(Experimental)This arg will override the default "
             "audio conversion command. "
             "Need to follow the references keyword argument. "
             "Default command to process the audio: "
             "{dft} "
             "(arg_num = 1)".format(
                 dft=constants.DEFAULT_AUDIO_CVT)
    )

    audio_prcs_group.add_argument(
        '-asc', '--audio-split-cmd',
        metavar='command',
        help="(Experimental)This arg will override the default "
             "audio split command. "
             "Need to follow the references keyword argument. "
             "Default command to process the audio: "
             "{dft} "
             "(arg_num = 1)".format(
                 dft=constants.DEFAULT_AUDIO_SPLT)
    )

    audio_prcs_group.add_argument(
        '-asf', '--api-suffix',
        metavar='file_suffix',
        default='.flac',
        help="(Experimental)This arg will override the default "
             "api audio suffix. "
             "(arg_num = 1) (default: %(default)s)"
    )

    audio_prcs_group.add_argument(
        '-asr', '--api-sample-rate',
        metavar='sample_rate',
        type=int,
        default=44100,
        help="(Experimental)This arg will override the default "
             "api audio sample rate, "
             "which control the audio sample rate "
             "before sending it to the api."
             "(arg_num = 1) (default: %(default)s)"
    )

    audio_prcs_group.add_argument(
        '-aac', '--api-audio-channel',
        metavar='channel_num',
        type=int,
        default=1,
        help="(Experimental)This arg will override the default "
             "api audio audio channel, "
             "which control the audio channel "
             "before sending it to the api."
             "(arg_num = 1) (default: %(default)s)"
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
        help="Minimum region size. "
             "Same docs above. "
             "(arg_num = 1) (default: %(default)s)"
    )

    auditok_group.add_argument(
        '-mxrs', '--max-region-size',
        metavar='second',
        type=float,
        default=constants.MAX_REGION_SIZE,
        help="Maximum region size. "
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
        help="""List all available subtitles formats.
                If your format is not supported,
                you can use ffmpeg or SubtitleEdit to convert the formats. 
                You need to offer fps option 
                when input is an audio file
                and output is \"sub\" format.
                (arg_num = 0)"""
    )

    list_group.add_argument(
        '-lsc', '--list-speech-codes',
        metavar='lang_code',
        const=' ',
        nargs='?',
        help="""List recommended \"-S\"/\"--speech-language\"
                Google Speech V2 language codes.
                If no arg is given, list all.
                Or else will list get a group of \"good match\"
                of the arg. Default \"good match\" standard is whose
                match score above 90(score between 0 and 100).
                Ref: https://tools.ietf.org/html/bcp47
                https://github.com/LuminosoInsight/langcodes/blob/master/langcodes/__init__.py
                lang code example: language-script-region-variant-extension-privateuse
                (arg_num = 0 or 1)"""
    )

    list_group.add_argument(
        '-ltc', '--list-translation-codes',
        metavar='lang_code',
        const=' ',
        nargs='?',
        help="""List all available \"-SRC\"/\"--src-language\"
                py-googletrans translation language codes.
                Or else will list get a group of \"good match\"
                of the arg. Default \"good match\" standard is whose
                match score above 90(score between 0 and 100).
                Same docs above. 
                (arg_num = 0 or 1)"""
    )

    list_group.add_argument(
        '-dsl', '--detect-sub-language',
        metavar='path',
        help="Use googletrans to detect a sub file's first line language. "
             "And list a group of matched language in recommended "
             "\"-S\"/\"--speech-language\" Google Speech V2 language codes. "
             "Ref: https://cloud.google.com/speech-to-text/docs/languages"
             "(arg_num = 1) (default: %(default)s)"
    )

    return parser.parse_args()
