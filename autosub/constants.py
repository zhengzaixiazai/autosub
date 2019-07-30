#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines constants used by autosub.
"""
# Import built-in modules
from __future__ import unicode_literals
import os
import sys
import locale

# Import third-party modules

# Any changes to the path and your own modules

SUPPORT_LOCALE = {
    "en_US",
    "zh_CN"
}
# Ref: https://www.gnu.org/software/gettext/manual/html_node/Locale-Names.html#Locale-Names

ENCODING = 'UTF-8'

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable executable'.
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(__file__)

LOCALE_PATH = os.path.abspath(os.path.join(APP_PATH, "data/locale"))

EXT_LOCALE = os.path.abspath(os.path.join(os.getcwd(), "locale"))
if os.path.isfile(EXT_LOCALE):
    with open(EXT_LOCALE, "r") as in_file:
        LINE = in_file.readline()
        LINE_LIST = LINE.split()
        if LINE_LIST[0] in SUPPORT_LOCALE:
            CURRENT_LOCALE = LINE_LIST[0]
        else:
            CURRENT_LOCALE = locale.getdefaultlocale()[0]
else:
    CURRENT_LOCALE = locale.getdefaultlocale()[0]

GOOGLE_SPEECH_V2_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
GOOGLE_SPEECH_V2_API_URL = \
    "www.google.com/speech-api/v2/recognize?client=chromium&lang={lang}&key={key}"
DEFAULT_CONCURRENCY = 10
DEFAULT_SRC_LANGUAGE = 'en-US'
DEFAULT_ENERGY_THRESHOLD = 45
MAX_REGION_SIZE = 6.0
MIN_REGION_SIZE = 0.5
DEFAULT_CONTINUOUS_SILENCE = 0.3
MAX_EXT_REGION_SIZE = 10
# Maximum speech to text region length in milliseconds
# when using external speech region control

DEFAULT_DST_LANGUAGE = 'en-US'
DEFAULT_LINES_PER_TRANS = 15
DEFAULT_SIZE_PER_TRANS = 4000
DEFAULT_SLEEP_SECONDS = 5

DEFAULT_SUBTITLES_FORMAT = 'srt'

DEFAULT_MODE_SET = {'regions', 'src', 'dst', 'bilingual'}
DEFAULT_SUB_MODE_SET = {'dst', 'bilingual'}
DEFAULT_LANG_MODE_SET = {'s', 'src', 'd'}
DEFAULT_AUDIO_PRCS_MODE_SET = {'o', 's', 'y', 'n'}

DEFAULT_AUDIO_PRCS = [
    "ffmpeg -hide_banner -i \"{in_}\" -af \"asplit[a],aphasemeter=video=0,\
ametadata=select:key=\
lavfi.aphasemeter.phase:value=-0.005:function=less,\
pan=1c|c0=c0,aresample=async=1:first_pts=0,[a]amix\" \
-ac 1 -f flac \"{out_}\"",
    "ffmpeg -hide_banner -i \"{in_}\" -af lowpass=3000,highpass=200 \"{out_}\"",
    "ffmpeg-normalize -v \"{in_}\" -ar 44100 -ofmt flac -c:a flac -pr -p -o \"{out_}\""
]

DEFAULT_AUDIO_CVT = "ffmpeg -hide_banner -y -i \"{in_}\" -ac {channel} -ar {sample_rate} \"{out_}\""

DEFAULT_AUDIO_SPLT = \
    "ffmpeg -ss {start} -t {dura} -y -i \"{in_}\" -c copy -loglevel error \"{out_}\""

DEFAULT_VIDEO_FPS_CMD = "ffprobe -v 0 -of csv=p=0 -select_streams" \
                        " v:0 -show_entries stream=r_frame_rate \"{in_}\""

SPEECH_TO_TEXT_LANGUAGE_CODES = {
    'af-za': 'Afrikaans (South Africa)',
    'am-et': 'Amharic (Ethiopia)',
    'ar-ae': 'Arabic (United Arab Emirates)',
    'ar-bh': 'Arabic (Bahrain)',
    'ar-dz': 'Arabic (Algeria)',
    'ar-eg': 'Arabic (Egypt)',
    'ar-il': 'Arabic (Israel)',
    'ar-iq': 'Arabic (Iraq)',
    'ar-jo': 'Arabic (Jordan)',
    'ar-kw': 'Arabic (Kuwait)',
    'ar-lb': 'Arabic (Lebanon)',
    'ar-ma': 'Arabic (Morocco)',
    'ar-om': 'Arabic (Oman)',
    'ar-ps': 'Arabic (State of Palestine)',
    'ar-qa': 'Arabic (Qatar)',
    'ar-sa': 'Arabic (Saudi Arabia)',
    'ar-tn': 'Arabic (Tunisia)',
    'az-az': 'Azerbaijani (Azerbaijan)',
    'bg-bg': 'Bulgarian (Bulgaria)',
    'bn-bd': 'Bengali (Bangladesh)',
    'bn-in': 'Bengali (India)',
    'ca-es': 'Catalan (Spain)',
    'cmn-hans-cn': 'Chinese, Mandarin (Simplified, China)',
    'cmn-hans-hk': 'Chinese, Mandarin (Simplified, Hong Kong)',
    'cmn-hant-tw': 'Chinese, Mandarin (Traditional, Taiwan)',
    'cs-cz': 'Czech (Czech Republic)',
    'da-dk': 'Danish (Denmark)',
    'de-de': 'German (Germany)',
    'el-gr': 'Greek (Greece)',
    'en-au': 'English (Australia)',
    'en-ca': 'English (Canada)',
    'en-gb': 'English (United Kingdom)',
    'en-gh': 'English (Ghana)',
    'en-ie': 'English (Ireland)',
    'en-in': 'English (India)',
    'en-ke': 'English (Kenya)',
    'en-ng': 'English (Nigeria)',
    'en-nz': 'English (New Zealand)',
    'en-ph': 'English (Philippines)',
    'en-sg': 'English (Singapore)',
    'en-tz': 'English (Tanzania)',
    'en-us': 'English (United States)',
    'en-za': 'English (South Africa)',
    'es-ar': 'Spanish (Argentina)',
    'es-bo': 'Spanish (Bolivia)',
    'es-cl': 'Spanish (Chile)',
    'es-co': 'Spanish (Colombia)',
    'es-cr': 'Spanish (Costa Rica)',
    'es-do': 'Spanish (Dominican Republic)',
    'es-ec': 'Spanish (Ecuador)',
    'es-es': 'Spanish (Spain)',
    'es-gt': 'Spanish (Guatemala)',
    'es-hn': 'Spanish (Honduras)',
    'es-mx': 'Spanish (Mexico)',
    'es-ni': 'Spanish (Nicaragua)',
    'es-pa': 'Spanish (Panama)',
    'es-pe': 'Spanish (Peru)',
    'es-pr': 'Spanish (Puerto Rico)',
    'es-py': 'Spanish (Paraguay)',
    'es-sv': 'Spanish (El Salvador)',
    'es-us': 'Spanish (United States)',
    'es-uy': 'Spanish (Uruguay)',
    'es-ve': 'Spanish (Venezuela)',
    'eu-es': 'Basque (Spain)',
    'fa-ir': 'Persian (Iran)',
    'fi-fi': 'Finnish (Finland)',
    'fil-ph': 'Filipino (Philippines)',
    'fr-ca': 'French (Canada)',
    'fr-fr': 'French (France)',
    'gl-es': 'Galician (Spain)',
    'gu-in': 'Gujarati (India)',
    'he-il': 'Hebrew (Israel)',
    'hi-in': 'Hindi (India)',
    'hr-hr': 'Croatian (Croatia)',
    'hu-hu': 'Hungarian (Hungary)',
    'hy-am': 'Armenian (Armenia)',
    'id-id': 'Indonesian (Indonesia)',
    'is-is': 'Icelandic (Iceland)',
    'it-it': 'Italian (Italy)',
    'ja-jp': 'Japanese (Japan)',
    'jv-id': 'Javanese (Indonesia)',
    'ka-ge': 'Georgian (Georgia)',
    'km-kh': 'Khmer (Cambodia)',
    'kn-in': 'Kannada (India)',
    'ko-kr': 'Korean (South Korea)',
    'lo-la': 'Lao (Laos)',
    'lt-lt': 'Lithuanian (Lithuania)',
    'lv-lv': 'Latvian (Latvia)',
    'ml-in': 'Malayalam (India)',
    'mr-in': 'Marathi (India)',
    'ms-my': 'Malay (Malaysia)',
    'nb-no': 'Norwegian Bokmal (Norway)',
    'ne-np': 'Nepali (Nepal)',
    'nl-nl': 'Dutch (Netherlands)',
    'pl-pl': 'Polish (Poland)',
    'pt-br': 'Portuguese (Brazil)',
    'pt-pt': 'Portuguese (Portugal)',
    'ro-ro': 'Romanian (Romania)',
    'ru-ru': 'Russian (Russia)',
    'si-lk': 'Sinhala (Sri Lanka)',
    'sk-sk': 'Slovak (Slovakia)',
    'sl-si': 'Slovenian (Slovenia)',
    'sr-rs': 'Serbian (Serbia)',
    'su-id': 'Sundanese (Indonesia)',
    'sv-se': 'Swedish (Sweden)',
    'sw-ke': 'Swahili (Kenya)',
    'sw-tz': 'Swahili (Tanzania)',
    'ta-in': 'Tamil (India)',
    'ta-lk': 'Tamil (Sri Lanka)',
    'ta-my': 'Tamil (Malaysia)',
    'ta-sg': 'Tamil (Singapore)',
    'te-in': 'Telugu (India)',
    'th-th': 'Thai (Thailand)',
    'tr-tr': 'Turkish (Turkey)',
    'uk-ua': 'Ukrainian (Ukraine)',
    'ur-in': 'Urdu (India)',
    'ur-pk': 'Urdu (Pakistan)',
    'vi-vn': 'Vietnamese (Vietnam)',
    'yue-hant-hk' : 'Chinese, Cantonese (Traditional, Hong Kong)',
    'zu-za': 'Zulu (South Africa)'
}

TRANSLATION_LANGUAGE_CODES = {
    'af': 'Afrikaans',
    'am': 'Amharic',
    'ar': 'Arabic',
    'az': 'Azerbaijani',
    'be': 'Belarusian',
    'bg': 'Bulgarian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'co': 'Corsican',
    'cs': 'Czech',
    'cy': 'Welsh',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'eo': 'Esperanto',
    'es': 'Spanish',
    'et': 'Estonian',
    'eu': 'Basque',
    'fa': 'Persian',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'ga': 'Irish',
    'gd': 'Scots Gaelic',
    'gl': 'Galician',
    'gu': 'Gujarati',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hr': 'Croatian',
    'ht': 'Haitian Creole',
    'hu': 'Hungarian',
    'hy': 'Armenian',
    'id': 'Indonesian',
    'ig': 'Igbo',
    'is': 'Icelandic',
    'it': 'Italian',
    'iw': 'Hebrew',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'ka': 'Georgian',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'kn': 'Kannada',
    'ko': 'Korean',
    'ku': 'Kurdish',
    'ky': 'Kyrgyz',
    'la': 'Latin',
    'lb': 'Luxembourgish',
    'lo': 'Lao',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'mg': 'Malagasy',
    'mi': 'Maori',
    'mk': 'Macedonian',
    'ml': 'Malayalam',
    'mn': 'Mongolian',
    'mr': 'Marathi',
    'ms': 'Malay',
    'mt': 'Maltese',
    'my': 'Myanmar(Burmese)',
    'ne': 'Nepali',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'ny': 'Nyanja(Chichewa)',
    'pa': 'Punjabi',
    'pl': 'Polish',
    'ps': 'Pashto',
    'pt': 'Portuguese(Portugal,Brazil)',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sd': 'Sindhi',
    'si': 'Sinhala(Sinhalese)',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'sm': 'Samoan',
    'sn': 'Shona',
    'so': 'Somali',
    'sq': 'Albanian',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'su': 'Sundanese',
    'sv': 'Swedish',
    'sw': 'Swahili',
    'ta': 'Tamil',
    'te': 'Telugu',
    'tg': 'Tajik',
    'th': 'Thai',
    'tl': 'Tagalog(Filipino)',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zh': 'Chinese (Simplified)',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'zu': 'Zulu'
}

OUTPUT_FORMAT = {
    'srt': 'SubRip',
    'ass': 'Advanced SubStation Alpha',
    'ssa': 'SubStation Alpha',
    'sub': 'MicroDVD Subtitle',
    'mpl2.txt': 'Similar to MicroDVD',
    'tmp': 'TMP Player Subtitle Format',
    'vtt': 'WebVTT',
    'json': 'json(Only times and text)',
    'ass.json': 'json(Complex ass content json)',
    'txt': 'Plain Text(Text or times)'
}

INPUT_FORMAT = {
    'srt': 'SubRip',
    'ass': 'Advanced SubStation Alpha',
    'ssa': 'SubStation Alpha',
    'sub': 'MicroDVD Subtitle',
    'txt': 'Similar to MicroDVD(mpl2)',
    'tmp': 'TMP Player Subtitle Format',
    'json': 'json(Complex ass content json)'
}
