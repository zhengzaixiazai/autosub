#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's metadata.
"""
# Import built-in modules
from __future__ import unicode_literals

# Any changes to the path and your own modules

_ = str
# For gettext po files

NAME = 'autosub'
VERSION = '0.5.4-alpha'
DESCRIPTION = _('Auto-generate subtitles for video/audio/subtitles file.')
LONG_DESCRIPTION = (
    _('Autosub is an automatic subtitles generating utility. '
      'It can detect speech regions automatically '
      'by using Auditok, split the audio files according to regions '
      'by using ffmpeg, '
      'transcribe speech based on several speech APIs and '
      'translate the subtitles\' text by using py-googletrans.'))
AUTHOR = 'Bing Ling'
AUTHOR_EMAIL = 'binglinggroup@outlook.com'
HOMEPAGE = 'https://github.com/BingLingGroup/autosub'
