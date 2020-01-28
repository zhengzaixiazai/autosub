#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's command line options.
"""
# Import built-in modules
from __future__ import absolute_import, print_function, unicode_literals
import argparse
import gettext

# Import third-party modules


# Any changes to the path and your own modules
from autosub import metadata
from autosub import constants

OPTIONS_TEXT = gettext.translation(domain=__name__,
                                   localedir=constants.LOCALE_PATH,
                                   languages=[constants.CURRENT_LOCALE],
                                   fallback=True)

META_TEXT = gettext.translation(domain=metadata.__name__,
                                localedir=constants.LOCALE_PATH,
                                languages=[constants.CURRENT_LOCALE],
                                fallback=True)

try:
    _ = OPTIONS_TEXT.ugettext
    M_ = META_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = OPTIONS_TEXT.gettext
    M_ = META_TEXT.gettext


def get_cmd_args():  # pylint: disable=too-many-statements
    """
    Get command-line arguments.
    """

    parser = argparse.ArgumentParser(
        prog=metadata.NAME,
        usage=_('\n  %(prog)s [-i path] [options]'),
        description=M_(metadata.DESCRIPTION),
        epilog=_("Make sure the argument with space is in quotes.\n"
                 "The default value is used\n"
                 "when the option is not given at the command line.\n"
                 "\"(arg_num)\" means if the option is given,\n"
                 "the number of the arguments is required.\n"
                 "Author: {author}\n"
                 "Email: {email}\n"
                 "Bug report: https://github.com/agermanidis/autosub\n").format(
                     author=metadata.AUTHOR,
                     email=metadata.AUTHOR_EMAIL),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    input_group = parser.add_argument_group(
        _('Input Options'),
        _('Options to control input.'))
    lang_group = parser.add_argument_group(
        _('Language Options'),
        _('Options to control language.'))
    output_group = parser.add_argument_group(
        _('Output Options'),
        _('Options to control output.'))
    speech_group = parser.add_argument_group(
        _('Speech Options'),
        _('Options to control speech-to-text. '
          'If Speech Options not given, it will only generate the times.'))
    pygt_group = parser.add_argument_group(
        _('py-googletrans Options'),
        _('Options to control translation. '
          'Default method to translate. '
          'Could be blocked at any time.'))
    gtv2_group = parser.add_argument_group(
        _('Google Translate V2 Options'),
        _('Options to control translation.(Not been tested) '
          'If the API key is given, '
          'it will replace the py-googletrans method.'))
    network_group = parser.add_argument_group(
        _('Network Options'),
        _('Options to control network.'))
    options_group = parser.add_argument_group(
        _('Other Options'),
        _('Other options to control.'))
    audio_prcs_group = parser.add_argument_group(
        _('Audio Processing Options'),
        _('Options to control audio processing.'))
    auditok_group = parser.add_argument_group(
        _('Auditok Options'),
        _('Options to control Auditok '
          'when not using external speech regions control.'))
    list_group = parser.add_argument_group(
        _('List Options'),
        _('List all available arguments.'))

    input_group.add_argument(
        '-i', '--input',
        metavar=_('path'),
        help=_("The path to the video/audio/subtitles file "
               "that needs to generate subtitles. "
               "When it is a subtitles file, "
               "the program will only translate it. "
               "(arg_num = 1)")
    )

    input_group.add_argument(
        '-er', '--ext-regions',
        metavar=_('path'),
        help=_("Path to the subtitles file "
               "which provides external speech regions, "
               "which is one of the formats that pysubs2 supports "
               "and overrides the default method to find speech regions. "
               "(arg_num = 1)")
    )

    input_group.add_argument(
        '-sty', '--styles',
        nargs='?', metavar=_('path'),
        const=' ',
        help=_("Valid when your output format is \"ass\"/\"ssa\". "
               "Path to the subtitles file "
               "which provides \"ass\"/\"ssa\" styles for your output. "
               "If the arg_num is 0, "
               "it will use the styles from the : "
               "\"-esr\"/\"--external-speech-regions\". "
               "More info on \"-sn\"/\"--styles-name\". "
               "(arg_num = 0 or 1)")
    )

    input_group.add_argument(
        '-sn', '--styles-name',
        nargs='*', metavar=_('style-name'),
        help=_("Valid when your output format is \"ass\"/\"ssa\" "
               "and \"-sty\"/\"--styles\" is given. "
               "Adds \"ass\"/\"ssa\" styles to your events. "
               "If not provided, events will use the first one "
               "from the file. "
               "If the arg_num is 1, events will use the "
               "specific style from the arg of \"-sty\"/\"--styles\". "
               "If the arg_num is 2, src language events use the first. "
               "Dst language events use the second. "
               "(arg_num = 1 or 2)")
    )

    lang_group.add_argument(
        '-S', '--speech-language',
        metavar=_('lang_code'),
        help=_("Lang code/Lang tag for speech-to-text. "
               "Recommend using the Google Cloud Speech reference "
               "lang codes. "
               "WRONG INPUT WON'T STOP RUNNING. "
               "But use it at your own risk. "
               "Ref: https://cloud.google.com/speech-to-text/docs/languages"
               "(arg_num = 1) (default: %(default)s)")
    )

    lang_group.add_argument(
        '-SRC', '--src-language',
        metavar=_('lang_code'),
        help=_("Lang code/Lang tag for translation source language. "
               "If not given, use langcodes-py2 to get a best matching "
               "of the \"-S\"/\"--speech-language\". "
               "If using py-googletrans as the method to translate, "
               "WRONG INPUT STOP RUNNING. "
               "(arg_num = 1) (default: %(default)s)")
    )

    lang_group.add_argument(
        '-D', '--dst-language',
        metavar=_('lang_code'),
        help=_("Lang code/Lang tag for translation destination language. "
               "Same attention in the \"-SRC\"/\"--src-language\". "
               "(arg_num = 1) (default: %(default)s)")
    )

    lang_group.add_argument(
        '-bm', '--best-match',
        metavar=_('mode'),
        nargs="*",
        help=_("Allow langcodes-py2 to get a best matching lang code "
               "when your input is wrong. "
               "Only functional for py-googletrans and Google Speech V2. "
               "Available modes: "
               "s, src, d, all. "
               "\"s\" for \"-S\"/\"--speech-language\". "
               "\"src\" for \"-SRC\"/\"--src-language\". "
               "\"d\" for \"-D\"/\"--dst-language\". "
               "(3 >= arg_num >= 1)")
    )

    lang_group.add_argument(
        '-mns', '--min-score',
        metavar='integer',
        type=int,
        help=_("An integer between 0 and 100 "
               "to control the good match group of "
               "\"-lsc\"/\"--list-speech-codes\" "
               "or \"-ltc\"/\"--list-translation-codes\" "
               "or the match result in \"-bm\"/\"--best-match\". "
               "Result will be a group of \"good match\" "
               "whose score is above this arg. "
               "(arg_num = 1)")
    )

    output_group.add_argument(
        '-o', '--output',
        metavar=_('path'),
        help=_("The output path for subtitles file. "
               "(default: the \"input\" path combined "
               "with the proper name tails) (arg_num = 1)")
    )

    output_group.add_argument(
        '-F', '--format',
        metavar=_('format'),
        help=_("Destination subtitles format. "
               "If not provided, use the extension "
               "in the \"-o\"/\"--output\" arg. "
               "If \"-o\"/\"--output\" arg doesn't provide "
               "the extension name, use \"{dft}\" instead. "
               "In this case, if \"-i\"/\"--input\" arg is a subtitles file, "
               "use the same extension from the subtitles file. "
               "(arg_num = 1) (default: {dft})").format(
                   dft=constants.DEFAULT_SUBTITLES_FORMAT)
    )

    output_group.add_argument(
        '-y', '--yes',
        action='store_true',
        help=_("Prevent pauses and allow files to be overwritten. "
               "Stop the program when your args are wrong. (arg_num = 0)")
    )

    output_group.add_argument(
        '-of', '--output-files',
        metavar=_('type'),
        nargs='*',
        default=["dst", ],
        help=_("Output more files. "
               "Available types: "
               "regions, src, dst, bilingual, all. "
               "(4 >= arg_num >= 1) (default: %(default)s)")
    )

    output_group.add_argument(
        '-fps', '--sub-fps',
        metavar='float',
        type=float,
        help=_("Valid when your output format is \"sub\". "
               "If input, it will override the fps check "
               "on the input file. "
               "Ref: https://pysubs2.readthedocs.io/en/latest/api-reference.html"
               "#supported-input-output-formats "
               "(arg_num = 1)")
    )

    output_group.add_argument(
        '-der', '--drop-empty-regions',
        action='store_true',
        help=_("Drop any regions without text. "
               "(arg_num = 0)")
    )

    speech_group.add_argument(
        '-sapi', '--speech-api',
        metavar=_('API_code'),
        default='gsv2',
        help=_("Choose which Speech-to-Text API to use. "
               "Currently supported: "
               "gsv2: Google Speech V2 (https://github.com/gillesdemey/google-speech-v2). "
               "gcsv1: Google Cloud Speech-to-Text V1P1Beta1 "
               "(https://cloud.google.com/speech-to-text/docs). "
               "(arg_num = 1) (default: %(default)s)"))

    speech_group.add_argument(
        '-skey', '--speech-key',
        metavar='key',
        help=_("The API key for Speech-to-Text API. (arg_num = 1) "
               "Currently supported: "
               "gsv2: The API key for gsv2. (default: Free API key) "
               "gcsv1: The API key for gcsv1. "
               "(Can be overridden by \"-sa\"/\"--service-account\")")
    )

    speech_group.add_argument(
        '-mnc', '--min-confidence',
        metavar='float',
        type=float,
        default=0.0,
        help=_("API response for text confidence. "
               "A float value between 0 and 1. "
               "Confidence bigger means the result is better. "
               "Input this argument will drop any result below it. "
               "Ref: https://github.com/BingLingGroup/google-speech-v2#response "
               "(arg_num = 1) (default: %(default)s)")
    )

    speech_group.add_argument(
        '-sc', '--speech-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help=_("Number of concurrent Speech-to-Text requests to make. "
               "(arg_num = 1) (default: %(default)s)")
    )

    pygt_group.add_argument(
        '-slp', '--sleep-seconds',
        metavar=_('second'),
        type=float,
        default=constants.DEFAULT_SLEEP_SECONDS,
        help=_("(Experimental)Seconds to sleep "
               "between two translation requests. "
               "(arg_num = 1) (default: %(default)s)")
    )

    pygt_group.add_argument(
        '-surl', '--service-urls',
        metavar='URL',
        nargs='*',
        help=_("(Experimental)Customize request urls. "
               "Ref: https://py-googletrans.readthedocs.io/en/latest/ "
               "(arg_num >= 1)")
    )

    pygt_group.add_argument(
        '-ua', '--user-agent',
        metavar='User-Agent headers',
        help=_("(Experimental)Customize User-Agent headers. "
               "Same docs above. "
               "(arg_num = 1)")
    )

    gtv2_group.add_argument(
        '-gtv2', '--gtransv2',
        metavar='key',
        help=_("The Google Translate V2 API key to be used. "
               "If not provided, use free API (py-googletrans) instead. "
               "(arg_num = 1)")
    )

    gtv2_group.add_argument(
        '-lpt', '--lines-per-trans',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_LINES_PER_TRANS,
        help=_("Number of lines per Google Translate V2 request. "
               "(arg_num = 1) (default: %(default)s)")
    )

    gtv2_group.add_argument(
        '-tc', '--trans-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help=_("Number of concurrent "
               "Google translate V2 API requests to make. "
               "(arg_num = 1) (default: %(default)s)")
    )

    network_group.add_argument(
        '-hsa', '--http-speech-api',
        action='store_true',
        help=_("Change the Google Speech V2 API "
               "URL into the http one. "
               "(arg_num = 0)")
    )

    network_group.add_argument(
        '-hsp', '--https-proxy',
        nargs='?', metavar='URL',
        const='https://127.0.0.1:1080',
        help=_("Add https proxy by setting environment variables. "
               "If arg_num is 0, use const proxy url. "
               "(arg_num = 0 or 1) (const: %(const)s)")
    )

    network_group.add_argument(
        '-hp', '--http-proxy',
        nargs='?', metavar='URL',
        const='http://127.0.0.1:1080',
        help=_("Add http proxy by setting environment variables. "
               "If arg_num is 0, use const proxy url. "
               "(arg_num = 0 or 1) (const: %(const)s)")
    )

    network_group.add_argument(
        '-pu', '--proxy-username',
        metavar=_('username'),
        help=_("Set proxy username. "
               "(arg_num = 1)")
    )

    network_group.add_argument(
        '-pp', '--proxy-password',
        metavar=_('password'),
        help=_("Set proxy password. "
               "(arg_num = 1)")
    )

    options_group.add_argument(
        '-h', '--help',
        action='help',
        help=_("Show %(prog)s help message and exit. (arg_num = 0)")
    )

    options_group.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s ' + metadata.VERSION
        + ' by ' + metadata.AUTHOR + ' <'
        + metadata.AUTHOR_EMAIL + '>',
        help=_("Show %(prog)s version and exit. (arg_num = 0)")
    )

    options_group.add_argument(
        '-sa', '--service-account',
        metavar=_('path'),
        help=_("Set service account key environment variable. "
               "It should be the file path of the JSON file "
               "that contains your service account credentials. "
               "If used, override the API key options. "
               "Ref: https://cloud.google.com/docs/authentication/getting-started "
               "Currently supported: gcsv1 (GOOGLE_APPLICATION_CREDENTIALS) "
               "(arg_num = 1)")
    )

    audio_prcs_group.add_argument(
        '-ap', '--audio-process',
        nargs='*', metavar=_('mode'),
        help=_("Option to control audio process. "
               "If not given the option, "
               "do normal conversion work. "
               "\"y\": pre-process the input first "
               "then start normal workflow. "
               "If succeed, no more conversion before "
               "the speech-to-text procedure. "
               "\"o\": only pre-process the input audio. "
               "(\"-k\"/\"--keep\" is true) "
               "\"s\": only split the input audio. "
               "(\"-k\"/\"--keep\" is true) "
               "Default command to pre-process the audio: "
               "{dft_1} | {dft_2} | {dft_3} "
               "(Ref: "
               "https://github.com/stevenj/autosub/blob/master/scripts/subgen.sh "
               "https://ffmpeg.org/ffmpeg-filters.html) "
               "(2 >= arg_num >= 1)").format(
                   dft_1=constants.DEFAULT_AUDIO_PRCS[0],
                   dft_2=constants.DEFAULT_AUDIO_PRCS[1],
                   dft_3=constants.DEFAULT_AUDIO_PRCS[2])
    )

    audio_prcs_group.add_argument(
        '-k', '--keep',
        action='store_true',
        help=_("Keep audio processing files to the output path. "
               "(arg_num = 0)")
    )

    audio_prcs_group.add_argument(
        '-apc', '--audio-process-cmd',
        nargs='*', metavar=_('command'),
        help=_("This arg will override the default "
               "audio pre-process command. "
               "Every line of the commands need to be in quotes. "
               "Input file name is {in_}. "
               "Output file name is {out_}. "
               "(arg_num >= 1)")
    )

    audio_prcs_group.add_argument(
        '-ac', '--audio-concurrency',
        metavar='integer',
        type=int,
        default=constants.DEFAULT_CONCURRENCY,
        help=_("Number of concurrent ffmpeg audio split process to make. "
               "(arg_num = 1) (default: %(default)s)")
    )

    audio_prcs_group.add_argument(
        '-acc', '--audio-conversion-cmd',
        metavar=_('command'),
        help=_("(Experimental)This arg will override the default "
               "audio conversion command. "
               "\"[\", \"]\" are optional arguments "
               "meaning you can remove them. "
               "\"{{\", \"}}\" are required arguments "
               "meaning you can't remove them. "
               "Default command to process the audio: "
               "{dft} "
               "(arg_num = 1)").format(
                   dft=constants.DEFAULT_AUDIO_CVT)
    )

    audio_prcs_group.add_argument(
        '-asc', '--audio-split-cmd',
        metavar=_('command'),
        help=_("(Experimental)This arg will override the default "
               "audio split command. "
               "Same attention above. "
               "Default: {dft} "
               "(arg_num = 1)").format(
                   dft=constants.DEFAULT_AUDIO_SPLT)
    )

    audio_prcs_group.add_argument(
        '-asf', '--api-suffix',
        metavar=_('file_suffix'),
        default='.flac',
        help=_("(Experimental)This arg will override the default "
               "API audio suffix. "
               "(arg_num = 1) (default: %(default)s)")
    )

    audio_prcs_group.add_argument(
        '-asr', '--api-sample-rate',
        metavar=_('sample_rate'),
        type=int,
        default=44100,
        help=_("(Experimental)This arg will override the default "
               "API audio sample rate(Hz). "
               "(arg_num = 1) (default: %(default)s)")
    )

    audio_prcs_group.add_argument(
        '-aac', '--api-audio-channel',
        metavar=_('channel_num'),
        type=int,
        default=1,
        help=_("(Experimental)This arg will override the default "
               "API audio channel. "
               "(arg_num = 1) (default: %(default)s)")
    )

    auditok_group.add_argument(
        '-et', '--energy-threshold',
        metavar=_('energy'),
        type=int,
        default=constants.DEFAULT_ENERGY_THRESHOLD,
        help=_("The energy level which determines the region to be detected. "
               "Ref: https://auditok.readthedocs.io/en/latest/apitutorial.html"
               "#examples-using-real-audio-data "
               "(arg_num = 1) (default: %(default)s)")
    )

    auditok_group.add_argument(
        '-mnrs', '--min-region-size',
        metavar=_('second'),
        type=float,
        default=constants.MIN_REGION_SIZE,
        help=_("Minimum region size. "
               "Same docs above. "
               "(arg_num = 1) (default: %(default)s)")
    )

    auditok_group.add_argument(
        '-mxrs', '--max-region-size',
        metavar=_('second'),
        type=float,
        default=constants.MAX_REGION_SIZE,
        help=_("Maximum region size. "
               "Same docs above. "
               "(arg_num = 1) (default: %(default)s)")
    )

    auditok_group.add_argument(
        '-mxcs', '--max-continuous-silence',
        metavar=_('second'),
        type=float,
        default=constants.DEFAULT_CONTINUOUS_SILENCE,
        help=_("Maximum length of a tolerated silence within a valid audio activity. "
               "Same docs above. "
               "(arg_num = 1) (default: %(default)s)")
    )

    auditok_group.add_argument(
        '-sml', '--strict-min-length',
        action='store_true',
        help=_("Ref: https://auditok.readthedocs.io/en/latest/core.html#class-summary "
               "(arg_num = 0)")
    )

    auditok_group.add_argument(
        '-dts', '--drop-trailing-silence',
        action='store_true',
        help=_("Ref: https://auditok.readthedocs.io/en/latest/core.html#class-summary "
               "(arg_num = 0)")
    )

    list_group.add_argument(
        '-lf', '--list-formats',
        action='store_true',
        help=_("List all available subtitles formats. "
               "If your format is not supported, "
               "you can use ffmpeg or SubtitleEdit to convert the formats. "
               "You need to offer fps option "
               "when input is an audio file "
               "and output is \"sub\" format. "
               "(arg_num = 0)")
    )

    list_group.add_argument(
        '-lsc', '--list-speech-codes',
        metavar=_('lang_code'),
        const=' ',
        nargs='?',
        help=_("List all recommended \"-S\"/\"--speech-language\" "
               "Google Speech-to-Text language codes. "
               "If no arg is given, list all. "
               "Or else will list get a group of \"good match\" "
               "of the arg. Default \"good match\" standard is whose "
               "match score above 90 (score between 0 and 100). "
               "Ref: https://tools.ietf.org/html/bcp47 "
               "https://github.com/LuminosoInsight/langcodes/blob/master/langcodes/__init__.py "
               "lang code example: language-script-region-variant-extension-privateuse "
               "(arg_num = 0 or 1)")
    )

    list_group.add_argument(
        '-ltc', '--list-translation-codes',
        metavar=_('lang_code'),
        const=' ',
        nargs='?',
        help=_("List all available \"-SRC\"/\"--src-language\" "
               "py-googletrans translation language codes. "
               "Or else will list get a group of \"good match\" "
               "of the arg. "
               "Same docs above. "
               "(arg_num = 0 or 1)")
    )

    list_group.add_argument(
        '-dsl', '--detect-sub-language',
        metavar=_('path'),
        help=_("Use py-googletrans to detect a sub file's first line language. "
               "And list a group of matched language in recommended "
               "\"-S\"/\"--speech-language\" Google Speech-to-Text language codes. "
               "Ref: https://cloud.google.com/speech-to-text/docs/languages "
               "(arg_num = 1) (default: %(default)s)")
    )

    return parser.parse_args()
