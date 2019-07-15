#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines speech and translation api used by autosub.
"""

from __future__ import absolute_import, unicode_literals

# Import built-in modules

# Import third-party modules
import json
import requests
from googleapiclient.discovery import build
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

# Any changes to the path and your own modules
from autosub import constants


class GoogleSpeechToTextV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text for an input FLAC file.
    """
    def __init__(self, api_url, language="en",
                 rate=44100, retries=3, api_key=constants.GOOGLE_SPEECH_V2_API_KEY):
        # pylint: disable=too-many-arguments
        self.language = language
        self.rate = rate
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for _ in range(self.retries):
                url = self.api_url.format(lang=self.language, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line = line['result'][0]['alternative'][0]['transcript']
                        return line[:1].upper() + line[1:]
                    except (JSONDecodeError, ValueError, IndexError):
                        # no result
                        continue

        except KeyboardInterrupt:
            return None


class GoogleTranslatorV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for translating a sentence from a one language to another.
    """
    def __init__(self, language, api_key, src, dst):
        self.language = language
        self.api_key = api_key
        self.service = build('translate', 'v2',
                             developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, sentence):
        try:
            if not sentence:
                return None

            result = self.service.translations().list( # pylint: disable=no-member
                source=self.src,
                target=self.dst,
                q=[sentence]
            ).execute()

            if 'translations' in result and result['translations'] and \
                    'translatedText' in result['translations'][0]:
                return result['translations'][0]['translatedText']

            return None

        except KeyboardInterrupt:
            return None
