#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's metadata.
"""

from __future__ import unicode_literals

# Import built-in modules
import gettext

# Any changes to the path and your own modules
from autosub import constants

META_TEXT = gettext.translation(domain=__name__,
                                localedir=constants.LOCALE_PATH,
                                languages=[constants.CURRENT_LOCALE],
                                fallback=True)

try:
    _ = META_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = META_TEXT.gettext

NAME = 'autosub'
VERSION = '0.4.1-alpha'
DESCRIPTION = 'Auto-generates subtitles for any video or audio file.'
LONG_DESCRIPTION = (
    'Autosub is a utility for automatic speech recognition,'
    'subtitle generation based on Google-Speech-v2 or Chrome-Web-Speech-api.'
    'It can also translate the subtitle\'s text by using googleapiclient.'
    'Currently not supports the latest Google Cloud APIs.'
)
AUTHOR = 'Anastasis Germanidis'
AUTHOR_EMAIL = 'agermanidis@gmail.com'
HOMEPAGE = 'https://github.com/agermanidis/autosub'
