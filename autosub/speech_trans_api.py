#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines speech and translation api used by autosub.
"""

from __future__ import absolute_import, unicode_literals

# Import built-in modules
import json
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

# Import third-party modules
import requests
from googleapiclient.discovery import build

# Any changes to the path and your own modules
from autosub import constants


class GoogleSpeechToTextV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text for an input FLAC file.
    """
    def __init__(self,
                 api_url,
                 min_confidence=0.0,
                 lang_code="en",
                 rate=44100,
                 api_key=constants.GOOGLE_SPEECH_V2_API_KEY,
                 retries=3):
        # pylint: disable=too-many-arguments
        self.min_confidence = min_confidence
        self.lang_code = lang_code
        self.rate = rate
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for _ in range(self.retries):
                url = self.api_url.format(lang=self.lang_code, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line_dict = line
                        line = line['result'][0]['alternative'][0]['transcript']
                    except (JSONDecodeError, ValueError, IndexError, KeyError):
                        # no result
                        continue

                    try:
                        confidence = float(line_dict['result'][0]['alternative'][0]['confidence'])
                        if confidence > self.min_confidence:
                            return line[:1].upper() + line[1:]
                        return ""
                    except KeyError:
                        # can't find confidence in json
                        # means it's 100% confident
                        return line[:1].upper() + line[1:]

        except KeyboardInterrupt:
            return None

        return ""


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
