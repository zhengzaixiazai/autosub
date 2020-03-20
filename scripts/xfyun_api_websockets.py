#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines xfyun API used by autosub.
"""

# Import built-in modules
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
from email.utils import formatdate
import time
import asyncio
from datetime import datetime
from time import mktime

# Import third-party modules
import websockets

# Any changes to the path and your own modules
from autosub import constants
from autosub import exceptions

try:
    import thread
except ImportError:
    import _thread as thread


def get_xfyun_transcript(
        result_dict):
    try:
        code = result_dict["code"]
        if code != 0:
            raise exceptions.SpeechToTextException(
                json.dumps(result_dict, indent=4, ensure_ascii=False))
        else:
            result = ""
            for item in result_dict["data"]["result"]["ws"]:
                result = result + item["cw"][0]["w"]
            return result
    except (KeyError, TypeError):
        return ""


def create_xfyun_url(
        api_key,
        api_secret,
        url=constants.XFYUN_SPEECH_WEBAPI_URL
):
    request_location = "/v2/iat"
    result_url = "wss://" + url + request_location
    now = datetime.now()
    stamp = mktime(now.timetuple())
    date = formatdate(timeval=stamp, localtime=False, usegmt=True)

    signature_origin = "host: " + url + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += "GET " + request_location + " HTTP/1.1"
    signature_sha = hmac.new(
        api_secret.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256).digest()

    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"{api_key}\", " \
                           "algorithm=\"hmac-sha256\", " \
                           "headers=\"host date request-line\", " \
                           "signature=\"{sign}\"".format(
                               api_key=api_key,
                               sign=signature_sha)
    authorization = base64.b64encode(
        authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    v = {
        "authorization": authorization,
        "date": date,
        "host": url
    }
    result_url = result_url + '?' + urlencode(v)
    return result_url


async def xfyun_speech_websocket(
        url,
        app_id,
        filename,
        business_args,
        is_full_result=False):
    data = {"status": 0,
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
            "audio": ""}
    common_args = {"app_id": app_id}
    business_args = business_args

    transcript = ""
    result_list = []

    try:
        async with websockets.connect(url) as web_socket:
            frame_size = 1280  # 每一帧的音频大小
            interval = 0.04  # 发送音频间隔(单位:s)
            status = 0  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
            with open(filename, "rb") as fp:
                while True:
                    buf = fp.read(frame_size)
                    # 文件结束
                    if not buf:
                        status = 2
                    data["audio"] = str(base64.b64encode(buf), "utf-8")
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == 0:
                        data["status"] = 0
                        web_socket_data = {
                            "common": common_args,
                            "business": business_args,
                            "data": data}
                        status = 1
                    # 中间帧处理
                    elif status == 1:
                        data["status"] = 1
                        web_socket_data = {"data": data}
                    # 最后一帧处理
                    elif status == 2:
                        data["status"] = 2
                        web_socket_data = {"data": data}
                        web_socket_json = json.dumps(web_socket_data)
                        await web_socket.send(web_socket_json)
                        try:
                            result = await web_socket.recv()
                            print(result)
                            web_socket_result = json.loads(result)
                            print(web_socket_result)
                        except (websockets.exceptions.ConnectionClosedOK, ValueError):
                            raise exceptions.SpeechToTextException("")

                        if not is_full_result:
                            transcript = transcript + get_xfyun_transcript(
                                web_socket_result)
                        else:
                            result_list.append(web_socket_result)
                        time.sleep(1)
                        break

                    web_socket_json = json.dumps(web_socket_data)
                    await web_socket.send(web_socket_json)
                    try:
                        result = await web_socket.recv()
                        print(result)
                        web_socket_result = json.loads(result)
                    except websockets.exceptions.ConnectionClosedOK:
                        raise exceptions.SpeechToTextException("")
                    except ValueError:
                        continue

                    if not is_full_result:
                        transcript = transcript + get_xfyun_transcript(
                            web_socket_result)
                    else:
                        result_list.append(web_socket_result)
                    # 模拟音频采样间隔
                    time.sleep(interval)

    except websockets.exceptions.InvalidStatusCode:
        raise exceptions.SpeechToTextException(websockets.exceptions.InvalidStatusCode)

    except exceptions.SpeechToTextException:
        if not is_full_result:
            return transcript
        else:
            return result_list


if __name__ == "__main__":
    print(asyncio.get_event_loop().run_until_complete(
        xfyun_speech_websocket(
            url=create_xfyun_url(api_key="",
                                 api_secret=""),
            app_id="",
            filename=r".pcm",
            business_args={
                "language": "zh_cn",
                "domain": "iat",
                "accent": "mandarin"
            }
        )
    ))
