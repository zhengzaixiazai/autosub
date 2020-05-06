#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines Baidu API used by autosub.
"""

# Import built-in modules
from urllib.parse import urlencode
import json
import gettext
import os
import base64

# Import third-party modules
import requests


# Any changes to the path and your own modules
from autosub import constants
from autosub import exceptions


API_BAIDU_TEXT = gettext.translation(domain=__name__,
                                     localedir=constants.LOCALE_PATH,
                                     languages=[constants.CURRENT_LOCALE],
                                     fallback=True)

_ = API_BAIDU_TEXT.gettext


def baidu_dev_pid_to_lang_code(
        dev_pid
):
    """
    Get lang code from a baidu_dev_pid.
    """
    if dev_pid == 1737:
        return "en"
    return "zh-cn"


def get_baidu_transcript(
        result_dict,
        delete_chars=None):
    """
    Function for getting transcript from Baidu ASR API result dictionary.
    Reference: https://ai.baidu.com/ai-doc/SPEECH/ek38lxj1u
    """
    try:
        err_no = result_dict["err_no"]
        if err_no != 0:
            if err_no not in (3301, 3303, 3307, 3313, 3315):
                raise exceptions.SpeechToTextException(
                    json.dumps(result_dict, indent=4, ensure_ascii=False))
            raise KeyError
        if delete_chars:
            result = result_dict["result"][0].translate(
                str.maketrans(delete_chars, " " * len(delete_chars)))
            return result.rstrip(" ")
        return result_dict["result"][0]
    except (KeyError, TypeError):
        return ""


def get_baidu_token(
        api_key,
        api_secret,
        token_url=constants.BAIDU_TOKEN_URL
):
    """
    Function for getting Baidu ASR API token
    """
    requests_params = {"grant_type": "client_credentials",
                       "client_id": api_key,
                       "client_secret": api_secret}
    post_data = urlencode(requests_params).encode("utf-8")
    result = requests.post(token_url, data=post_data)
    result_str = result.content.decode("utf-8")
    # get the one with valid content
    try:
        result_dict = json.loads(result_str)
        if "access_token" in result_dict and "scope" in result_dict:
            if "audio_voice_assistant_get" not in result_dict["scope"].split(" "):
                raise exceptions.SpeechToTextException(
                    _("Error: Check you project if its ASR feature is enabled."))
            return result_dict["access_token"]
        raise exceptions.SpeechToTextException(
            json.dumps(result_dict, indent=4, ensure_ascii=False))
    except (ValueError, IndexError):
        # no result
        return ""


class BaiduASRAPI:  # pylint: disable=too-few-public-methods
    """
    Class for performing Speech-to-Text using Baidu ASR API.
    """
    def __init__(self,
                 config,
                 api_url=constants.BAIDU_ASR_URL,
                 retries=3,
                 is_keep=False,
                 is_full_result=False,
                 delete_chars=None):
        # pylint: disable=too-many-arguments
        self.config = config
        self.api_url = api_url
        self.retries = retries
        self.is_keep = is_keep
        self.is_full_result = is_full_result
        self.delete_chars = delete_chars

    def __call__(self, filename):
        try:  # pylint: disable=too-many-nested-blocks
            audio_file = open(filename, mode="rb")
            audio_data = audio_file.read()
            audio_file.close()
            if not self.is_keep:
                os.remove(filename)

            for _ in range(self.retries):
                # Reference: https://github.com/Baidu-AIP/speech-demo/blob/master
                #            /rest-api-asr/python/asr_json.py
                self.config["speech"] = base64.b64encode(audio_data).decode('utf-8')
                self.config["len"] = len(audio_data)
                config_json = json.dumps(self.config, ensure_ascii=False)
                try:
                    requests_result = \
                        requests.post(self.api_url, data=config_json)
                except requests.exceptions.ConnectionError:
                    continue
                requests_result_json = requests_result.content.decode("utf-8")
                try:
                    result_dict = json.loads(requests_result_json)
                except ValueError:
                    # no result
                    continue

                if not self.is_full_result:
                    return get_baidu_transcript(result_dict, self.delete_chars)
                return result_dict

        except KeyboardInterrupt:
            return None

        return None


# if __name__ == "__main__":
#     # 测试时候在此处正确填写相关信息即可运行
#     config = {
#         'dev_pid': 1537,
#         'format': "pcm",
#         'rate': "16000",
#         'token': get_baidu_token(
#             api_key="",
#             api_secret=""),
#         'cuid': "python",
#         'channel': 1,
#     }
#
#     baidu_asr_obj = BaiduASRAPI(
#         api_url=constants.BAIDU_ASR_URL,
#         config=config,
#         is_full_result=False,
#         is_keep=True)
#
#     print(baidu_asr_obj(filename=r".pcm"))
