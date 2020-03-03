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

# Import third-party modules
import requests
from google.cloud import speech_v1p1beta1
from google.protobuf.json_format import MessageToDict

# Any changes to the path and your own modules
from autosub import exceptions


def get_google_speech_v2_transcript(
        min_confidence,
        result_dict):
    """
    Function for getting transcript from Google Speech-to-Text V2 json format string result.
    """
    if 'result' in result_dict and result_dict['result'] \
            and 'alternative' in result_dict['result'][0] \
            and result_dict['result'][0]['alternative'] \
            and 'transcript' in result_dict['result'][0]['alternative'][0]:
        text = result_dict['result'][0]['alternative'][0]['transcript']

        if 'confidence' in result_dict['result'][0]['alternative'][0]:
            confidence = \
                float(result_dict['result'][0]['alternative'][0]['confidence'])
            if confidence > min_confidence:
                result = text[:1].upper() + text[1:]
                result = result.replace('’', '\'')
                return result
            return None

        # can't find confidence in json
        # means it's 100% confident
        result = text[:1].upper() + text[1:]
        result = result.replace('’', '\'')
        return result

    return None


def get_gcsv1p1beta1_transcript(
        min_confidence,
        result_dict):
    """
    Function for getting transcript from Google Cloud Speech-to-Text V1P1Beta1 result dictionary.
    """
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

    # can't find confidence in json
    # means it's 100% confident
    result_dict = result_dict['transcript']
    result = result_dict[:1].upper() + result_dict[1:]
    result = result.replace('’', '\'')
    return result


class GoogleSpeechV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text using Google Speech V2 API for an input FLAC file.
    """
    def __init__(self,
                 api_url,
                 headers,
                 min_confidence=0.0,
                 retries=3,
                 is_keep=False,
                 is_full_result=False):
        # pylint: disable=too-many-arguments
        self.min_confidence = min_confidence
        self.retries = retries
        self.api_url = api_url
        self.is_keep = is_keep
        self.headers = headers
        self.is_full_result = is_full_result

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

                if not self.is_full_result:
                    # receive several results delimited by LF
                    result_str = result.content.decode('utf-8').split("\n")
                    # get the one with valid content
                    for line in result_str:
                        try:
                            line_dict = json.loads(line)
                            transcript = get_google_speech_v2_transcript(
                                self.min_confidence,
                                line_dict)
                            if transcript:
                                # make sure it is the valid transcript
                                return transcript

                        except (ValueError, IndexError):
                            # no result
                            continue

                else:
                    result_str = result.content.decode('utf-8').split("\n")
                    for line in result_str:
                        try:
                            line_dict = json.loads(line)
                            transcript = get_google_speech_v2_transcript(
                                self.min_confidence,
                                line_dict)
                            if transcript:
                                # make sure it is the result with valid transcript
                                return line_dict

                        except (ValueError, IndexError):
                            # no result
                            continue

                # Every line of the result can't be loaded to json
                return None

        except KeyboardInterrupt:
            return None

        return None


def gcsv1p1beta1_service_client(
        filename,
        is_keep,
        config,
        min_confidence,
        is_full_result=False):
    """
    Function for performing Speech-to-Text
    using Google Cloud Speech-to-Text V1P1Beta1 API client for an input FLAC file.
    """
    try:  # pylint: disable=too-many-nested-blocks
        audio_file = open(filename, mode='rb')
        audio_data = audio_file.read()
        audio_file.close()
        if not is_keep:
            os.remove(filename)

        # https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries
        # https://cloud.google.com/speech-to-text/docs/basics
        # https://cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1p1beta1#google.cloud.speech.v1p1beta1.SpeechRecognitionResult
        client = speech_v1p1beta1.SpeechClient()
        audio_dict = {"content": audio_data}
        recognize_reponse = client.recognize(config, audio_dict)
        result_dict = MessageToDict(
            recognize_reponse,
            preserving_proto_field_name=True)

        if not is_full_result:
            return get_gcsv1p1beta1_transcript(min_confidence, result_dict)
        return result_dict

    except KeyboardInterrupt:
        return None


class GCSV1P1Beta1URL(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing Speech-to-Text
    using Google Cloud Speech-to-Text V1P1Beta1 API URL for an input FLAC file.
    """
    def __init__(self,
                 config,
                 api_url=None,
                 headers=None,
                 min_confidence=0.0,
                 retries=3,
                 is_keep=False,
                 is_full_result=False):
        # pylint: disable=too-many-arguments
        self.config = config
        self.api_url = api_url
        self.headers = headers
        self.min_confidence = min_confidence
        self.retries = retries
        self.is_keep = is_keep
        self.is_full_result = is_full_result

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

                try:
                    requests_result = \
                        requests.post(self.api_url, data=config_json, headers=self.headers)

                except requests.exceptions.ConnectionError:
                    continue

                requests_result_json = requests_result.content.decode('utf-8')

                try:
                    result_dict = json.loads(requests_result_json)
                except ValueError:
                    # no result
                    continue

                if not self.is_full_result:
                    return get_gcsv1p1beta1_transcript(self.min_confidence, result_dict)
                return result_dict

        except KeyboardInterrupt:
            return None

        return None
