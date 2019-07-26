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
DESCRIPTION = _('Auto-generates subtitles for video/audio/subtitles file.')
LONG_DESCRIPTION = (
    _('Autosub is an automatic subtitles generating utility. '
      'It can detect speech regions automatically '
      'by using Auditok, split the audio files according to regions '
      'by using ffmpeg, '
      'transcribe speech based on Chrome-Web-Speech-api and '
      'translate the subtitles\' text by using py-googletrans. '
      'It currently not supports the latest Google Cloud APIs.')
)
AUTHOR = 'Anastasis Germanidis'
AUTHOR_EMAIL = 'agermanidis@gmail.com'
HOMEPAGE = 'https://github.com/agermanidis/autosub'
