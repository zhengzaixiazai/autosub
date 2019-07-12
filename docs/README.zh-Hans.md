# Autosub

<escape><a href="https://travis-ci.org/BingLingGroup/autosub"><img src="https://travis-ci.org/BingLingGroup/autosub.svg?branch=alpha"></img></a></escape>

[English](../README.md)

本仓库不同于[原仓库](https://github.com/agermanidis/autosub)。

本仓库由多人修改过，请查看[更新日志](CHANGELOG.zh-Hans.md)。

<escape><img src="../docs/icon/autosub.png" width="128px"></escape>

[autosub图标](docs/icon/autosub.svg)由冰灵制作。

软件: [inkscape](https://inkscape.org/zh/)

字体: [思源黑体](https://github.com/adobe-fonts/source-han-sans) ([SIL](https://github.com/adobe-fonts/source-han-sans/blob/master/LICENSE.txt))

颜色: [Solarized](https://en.wikipedia.org/wiki/Solarized_(color_scheme)#Colors)

### 目录

1. [介绍](#介绍)
   - 1.1 [输入](#输入)
   - 1.2 [分割](#分割)
   - 1.3 [语音转文字/翻译API请求](#语音转文字翻译api请求)
   - 1.4 [语音转文字/翻译语言支持](#语音转文字翻译语言支持)
   - 1.5 [输出](#输出)
2. [许可](#许可)
3. [下载与安装](#下载与安装)
   - 3.1 [分支](#分支)
   - 3.2 [在Ubuntu上安装](#在ubuntu上安装)
   - 3.3 [在Windows上安装](#在windows上安装)
4. [使用方法](#使用方法)

点击上箭头以返回目录。

### 介绍

Autosub是一个使用[Google-Speech-v2](https://github.com/gillesdemey/google-speech-v2)或者说[Chrome-Web-Speech-api](https://github.com/agermanidis/autosub/issues/1)来将语音转录为文字的程序。它也能通过[googleapiclient](http://googleapis.github.io/google-api-python-client/docs/epy/index.html)来对字幕进行翻译。目前不支持最新的Google Cloud API。

#### 输入

ffmpeg支持的视频或者音频文件。程序会使用ffmpeg来将相关文件的格式转换为[API支持的格式](https://github.com/gillesdemey/google-speech-v2#data)。

#### 分割

因为语音转文字API只支持10到15秒这样的[短片段音频](https://github.com/gillesdemey/google-speech-v2#caveats)，我们需要将音频文件分割为若干包含语音的小片段。

使用一小段声音(4096帧长度，16000采样率大概0.256秒)的平均功率作为瞬时功率作为强度来寻找语音区域。

或者使用外部文件提供的时间码来作为语音区域输入，支持pysubs2支持的文件格式，如`.ass`或者`.srt`。这样你就可以使用外部工具先制作时间轴然后让程序使用并得到精确度更高的识别结果。

- 为了进一步提高识别率，有必要对音频进行[预处理](https://github.com/agermanidis/autosub/issues/40)。

#### 语音转文字/翻译API请求

使用python的多进程库对API请求进行并行化处理，来加速转录速度。

- 可能需要对字幕文件行进行后处理，某些行可能长度过长，导致无法被放在视频画面长度中的同一行。

(可选)把字幕翻译成别的语言，最后再把结果保存在本地。

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

#### 语音转文字/翻译语言支持

语音转文字的语言代码和翻译的语言代码是不一样的，因为这俩API并不相同。

本程序允许使用的语言代码，你可以通过输入参数`-lsc`或者`--list-speech-to-text-codes`以及`-ltc`或者`--list-translation-codes`来获得。或者你也可以打开[constants.py](../autosub/constants.py)来查看。

- 目前允许使用的语言代码是被硬编码在代码里面的，你在运行时无法更改，这样是为了防止任何由于模糊的预言代码导致的不准确的识别结果。当你输入模糊的语言代码时，谷歌会根据你的IP地址进行本地化识别，这对于使用者来讲是不可控制的。

#### 输出

目前支持的输出格式有`.srt`，`.vtt`，`.json`，`.raw`(也就是Aegisub的纯文本输出格式)。

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

### 许可

**[注意]**: 本仓库和[原仓库](https://github.com/agermanidis/autosub)使用的许可不一样。

[GPLv3](LICENSE)

MIT对GPLv3是兼容的，GPLv3对MIT不兼容。

### 下载与安装

**[注意]**: 除去PyPI版本的代码和原仓库的一致，其他的安装方式均包含非原仓库的代码。

#### 分支

[alpha分支](https://github.com/BingLingGroup/autosub/tree/alpha)

- 包括大量在[原仓库代码](https://github.com/agermanidis/autosub)基础上的改动. 详见[更新日志](CHANGELOG.zh-Hans.md)。

[dev分支](https://github.com/BingLingGroup/autosub/tree/dev)

- 不包含[alpha分支](https://github.com/BingLingGroup/autosub/tree/alpha)中添加的新功能，仅包含最少的改动来让程序能在Windows上正常运行，而不是像[原仓库](https://github.com/agermanidis/autosub)的版本那样遇到各种各样的问题。

其他分支

- 只被用来测试或者提出拉取请求。除非你知道自己在干什么，否则不要安装它们。

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

#### 在Ubuntu上安装

**[注意]**: 第一行包含依赖的安装。

从PyPI安装。

```bash
apt install ffmpeg python python-pip -y
pip install autosub
```

从`dev`分支安装。

```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@dev
```

从`alpha`分支安装。

```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

#### 在Windows上安装

你可以直接去[发布页](https://github.com/BingLingGroup/autosub/releases)下载Windows的最新发布版。

- **[注意]**: 目前的autosub提前发布版是由pyinstaller打包的，意味着它的运行速度可能会有点慢。以后会推出nuitka编译版。

或者从choco上安装。

命令行安装choco的指令如下。

```batch
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
```

从`dev`分支安装。

```batch
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@dev
```

从`alpha`分支安装。

```batch
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

### 使用方法

对于原版autosub的使用，可以参见这篇[简体中文使用指南](https://binglinggroup.github.io/archives/autosub安装使用指南(windows及ubuntu).html)。

对于alpha分支autosub的使用，可以参考以下帮助信息

```bash
$ autosub -h
usage: autosub [-h] [-C CONCURRENCY] [-o OUTPUT] [-esr [path]] [-F FORMAT]
               [-S SRC_LANGUAGE] [-D DST_LANGUAGE] [-K API_KEY] [-lf] [-lsc]
               [-ltc] [-htp]
               [source_path]

positional arguments:
  source_path           Path to the video or audio file to subtitle

optional arguments:
  -h, --help            show this help message and exit
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
  -o OUTPUT, --output OUTPUT
                        Output path for subtitles (by default, subtitles are
                        saved in the same directory and name as the source
                        path)
  -esr [path], --external-speech-regions [path]
                        Path to the external speech regions, which is one of
                        the formats that pysubs2 supports and overrides the
                        default method to find speech regions
  -F FORMAT, --format FORMAT
                        Destination subtitle format
  -S SRC_LANGUAGE, --src-language SRC_LANGUAGE
                        Language spoken in source file
  -D DST_LANGUAGE, --dst-language DST_LANGUAGE
                        Desired language for the subtitles
  -K API_KEY, --api-key API_KEY
                        The Google Translation API key to be used. (Required
                        for subtitle translation)
  -lf, --list-formats   List all available subtitle formats
  -lsc, --list-speech-to-text-codes
                        List all available source language codes, which mean
                        the speech-to-text available language codes.
                        [WARNING]: Its name format is different from the
                        destination language codes. And it's Google who make
                        that difference not the developers of the autosub.
                        Reference: https://cloud.google.com/speech-to-
                        text/docs/languages
  -ltc, --list-translation-codes
                        List all available destination language codes, which
                        mean the translation language codes. [WARNING]: Its
                        name format is different from the source language
                        codes. And it's Google who make that difference not
                        the developers of the autosub. Reference:
                        https://cloud.google.com/translate/docs/languages
  -htp, --http-speech-to-text-api
                        Change the speech-to-text api url into the http one
```

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>
