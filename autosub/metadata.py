#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's metadata.
"""

from __future__ import unicode_literals

# Import built-in modules

# Any changes to the path and your own modules

NAME = 'autosub'
VERSION = '0.4.1-alpha'
DESCRIPTION = 'Auto-generates subtitles for video/audio/subtitles file.'
LONG_DESCRIPTION = (
    'Autosub is an automatic subtitles generating utility. '
    'It can detect speech regions automatically '
    'by using Auditok, split the audio files according to regions '
    'by using ffmpeg, '
    'transcribe speech based on Chrome-Web-Speech-api and '
    'translate the subtitles\' text by using py-googletrans. '
    'It currently not supports the latest Google Cloud APIs.'
)
AUTHOR = 'Anastasis Germanidis'
AUTHOR_EMAIL = 'agermanidis@gmail.com'
HOMEPAGE = 'https://github.com/agermanidis/autosub'
