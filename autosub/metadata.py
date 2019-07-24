#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's metadata.
"""

from __future__ import unicode_literals

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

ENCODING = 'UTF-8'
LOCALE_PATH = '../data/locale'
