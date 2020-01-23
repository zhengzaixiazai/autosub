#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines speech and translation api used by autosub.
"""
# Import built-in modules
from __future__ import absolute_import, unicode_literals
import os
import base64
import json
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

# Import third-party modules
import requests
from googleapiclient.discovery import build
from google.cloud import speech_v1p1beta1
from google.protobuf.json_format import MessageToDict

# Any changes to the path and your own modules
from autosub import exceptions


class GoogleSpeechV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text using Google Speech V2 API for an input FLAC file.
    """
    def __init__(self,
                 api_url,
                 headers,
                 min_confidence=0.0,
                 retries=3,
                 is_keep=False):
        # pylint: disable=too-many-arguments
        self.min_confidence = min_confidence
        self.retries = retries
        self.api_url = api_url
        self.is_keep = is_keep
        self.headers = headers

    def __call__(self, filename):
        try:  # pylint: disable=too-many-nested-blocks
            audio_file = open(filename, mode='rb')
            audio_data = audio_file.read()
            audio_file.close()
            if not self.is_keep:
                os.remove(filename)
            for _ in range(self.retries):
                try:
                    result = requests.post(self.api_url, data=audio_data, headers=self.headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in result.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line_dict = line
                        if 'result' in line and line['result'] \
                                and 'alternative' in line['result'][0] \
                                and line['result'][0]['alternative'] \
                                and 'transcript' in line['result'][0]['alternative'][0]:
                            line = line['result'][0]['alternative'][0]['transcript']

                            if 'confidence' in line_dict['result'][0]['alternative'][0]:
                                confidence = \
                                    float(line_dict['result'][0]['alternative'][0]['confidence'])
                                if confidence > self.min_confidence:
                                    result = line[:1].upper() + line[1:]
                                    result = result.replace('’', '\'')
                                    return result
                                return None

                            else:
                                # can't find confidence in json
                                # means it's 100% confident
                                result = line[:1].upper() + line[1:]
                                result = result.replace('’', '\'')
                                return result

                    except (JSONDecodeError, ValueError, IndexError):
                        # no result
                        continue

        except KeyboardInterrupt:
            return None

        return None


def gcsv1p1beta1_service_client(
        filename,
        is_keep,
        config,
        min_confidence
):
    """
    Function for performing speech-to-text
    using Google Cloud Speech V1P1Beta1 API for an input FLAC file.
    """
    try:  # pylint: disable=too-many-nested-blocks
        audio_file = open(filename, mode='rb')
        audio_data = audio_file.read()
        audio_file.close()
        if not is_keep:
            os.remove(filename)

        # https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries
        # https://cloud.google.com/speech-to-text/docs/basics
        # https://cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1p1beta1
        client = speech_v1p1beta1.SpeechClient()
        audio_dict = {"content": audio_data}
        recognize_reponse = client.recognize(config, audio_dict)
        result_dict = MessageToDict(
            recognize_reponse,
            preserving_proto_field_name=True)

        if 'results' in result_dict and result_dict['results'] \
                and 'alternatives' in result_dict['results'][0] \
                and result_dict['results'][0]['alternatives'] \
                and 'transcript' in result_dict['results'][0]['alternatives'][0]:
            result_dict = result_dict['results'][0]['alternatives'][0]

            if 'transcript' not in result_dict:
                return None

        else:
            raise exceptions.SpeechToTextException(
                json.dumps(result_dict, indent=4, ensure_ascii=False))

        if 'confidence' in result_dict:
            confidence = \
                float(result_dict['confidence'])
            if confidence > min_confidence:
                result_dict = result_dict['transcript']
                result = result_dict[:1].upper() + result_dict[1:]
                result = result.replace('’', '\'')
                return result
            return None
        else:
            # can't find confidence in json
            # means it's 100% confident
            result_dict = result_dict['transcript']
            result = result_dict[:1].upper() + result_dict[1:]
            result = result.replace('’', '\'')
            return result

    except KeyboardInterrupt:
        return None


class GCSV1P1Beta1URL(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text
    using Google Cloud Speech V1P1Beta1 API for an input FLAC file.
    """
    def __init__(self,
                 config,
                 api_url=None,
                 headers=None,
                 min_confidence=0.0,
                 retries=3,
                 is_keep=False):
        # pylint: disable=too-many-arguments
        self.config = config
        self.api_url = api_url
        self.headers = headers
        self.min_confidence = min_confidence
        self.retries = retries
        self.is_keep = is_keep

    def __call__(self, filename):
        try:  # pylint: disable=too-many-nested-blocks
            audio_file = open(filename, mode='rb')
            audio_data = audio_file.read()
            audio_file.close()
            if not self.is_keep:
                os.remove(filename)

            for _ in range(self.retries):
                # https://cloud.google.com/speech-to-text/docs/quickstart-protocol
                # https://cloud.google.com/speech-to-text/docs/base64-encoding
                # https://gist.github.com/bretmcg/07e0efe27611d7039c2e4051b4354908
                audio_dict = \
                    {"content": base64.b64encode(audio_data).decode("utf-8")}
                request_data = {"config": self.config, "audio": audio_dict}
                config_json = json.dumps(request_data, ensure_ascii=False)
                requests_result = \
                    requests.post(self.api_url, data=config_json, headers=self.headers)
                requests_result_json = requests_result.content.decode('utf-8')

                try:
                    result_dict = json.loads(requests_result_json)
                except JSONDecodeError:
                    # no result
                    continue

                if 'results' in result_dict and result_dict['results'] \
                        and 'alternatives' in result_dict['results'][0] \
                        and result_dict['results'][0]['alternatives'] \
                        and 'transcript' in result_dict['results'][0]['alternatives'][0]:
                    result_dict = result_dict['results'][0]['alternatives'][0]

                    if 'transcript' not in result_dict:
                        return None

                else:
                    raise exceptions.SpeechToTextException(
                        requests_result_json)

                if 'confidence' in result_dict:
                    confidence = \
                        float(result_dict['confidence'])
                    if confidence > self.min_confidence:
                        result_dict = result_dict['transcript']
                        result = result_dict[:1].upper() + result_dict[1:]
                        result = result.replace('’', '\'')
                        return result
                    return None
                else:
                    # can't find confidence in json
                    # means it's 100% confident
                    result_dict = result_dict['transcript']
                    result = result_dict[:1].upper() + result_dict[1:]
                    result = result.replace('’', '\'')
                    return result

        except KeyboardInterrupt:
            return None

        return None


class GoogleTranslatorV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for GoogleTranslatorV2 translating text from one language to another.
    """
    def __init__(self, api_key, src, dst):
        self.api_key = api_key
        self.service = build('translate', 'v2',
                             developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, trans_list):
        try:
            if not trans_list:
                return None

            trans_str = '\n'.join(trans_list)

            result = self.service.translations().list(  # pylint: disable=no-member
                source=self.src,
                target=self.dst,
                q=[trans_str]
            ).execute()

            if 'translations' in result and result['translations'] and \
                    'translatedText' in result['translations'][0]:
                return '\n'.split(result['translations'][0]['translatedText'])

            return None

        except KeyboardInterrupt:
            return None
