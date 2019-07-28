# Autosub

<escape><a href="https://travis-ci.org/BingLingGroup/autosub"><img src="https://travis-ci.org/BingLingGroup/autosub.svg?branch=alpha"></img></a> <a href="https://app.fossa.io/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub"><img src="https://app.fossa.io/api/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub.svg?type=shield"></img></a></escape>

[简体中文](docs/README.zh-Hans.md)

This repo is not the same as [the original autosub repo](https://github.com/agermanidis/autosub).

This repo has been modified by several people. See the [Changelog](CHANGELOG.md).

<escape><img src="docs/icon/autosub.png" width="128px"></escape>

[autosub icon](docs/icon/autosub.svg) designed by BingLingGroup.

Software: [inkscape](https://inkscape.org/zh/)

Font: [source-han-sans](https://github.com/adobe-fonts/source-han-sans) ([SIL](https://github.com/adobe-fonts/source-han-sans/blob/master/LICENSE.txt))

Color: [Solarized](https://en.wikipedia.org/wiki/Solarized_(color_scheme)#Colors)

### TOC

1. [Description](#description)
2. [License](#license)
3. [Dependencies](dependencies)
4. [Download and Installation](#download-and-installation)
   - 4.1 [Branches](#branches)
   - 4.2 [Install on Ubuntu](#install-on-ubuntu)
   - 4.3 [Install on Windows](#install-on-windows)
5. [Workflow](#workflow)
   - 5.1 [Input](#input)
   - 5.2 [Divide](#divide)
   - 5.3 [Speech-to-Text/Translation API request](#speech-to-texttranslation-api-request)
   - 5.4 [Speech-to-Text/Translation language support](#speech-to-texttranslation-language-support)
   - 5.5 [Output](#Output)
6. [Usage](#usage)

Click up arrow to go back to TOC.

### Description

Autosub is an automatic subtitles generating utility. It can detect speech regions automatically by using Auditok, split the audio files according to regions by using ffmpeg, transcribe speech based on [Google-Speech-v2](https://github.com/gillesdemey/google-speech-v2)([Chrome-Web-Speech-api](https://github.com/agermanidis/autosub/issues/1)) and translate the subtitles' text by using py-googletrans. It currently not supports the latest Google Cloud APIs.

### License

**[ATTENTION]**: This repo has a different license from [the original repo](https://github.com/agermanidis/autosub).

[GPLv3](LICENSE)

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub?ref=badge_shield)

### Dependencies

Autosub depends on these third party softwares or python packages. Much appreciation to all of these projects.

- [ffmpeg](https://ffmpeg.org/)
- [auditok](https://github.com/amsehili/auditok)
- [pysubs2](https://github.com/tkarabela/pysubs2)
- [py-googletrans](https://github.com/ssut/py-googletrans)
- [langcodes](https://github.com/LuminosoInsight/langcodes)
- [ffmpeg-normalize](https://github.com/slhck/ffmpeg-normalize)
- ...

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### License

**[ATTENTION]**: This repo has a different license from [the original repo](https://github.com/agermanidis/autosub).

[GPLv3](LICENSE)

[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FBingLingGroup%2Fautosub)

### Download and Installation

**[ATTENTION]**: Except the PyPI version, others include non-original codes not from the original repository.

After autosub-0.4.0, all of the codes is compatible with both Python 2.7 and Python 3. The installation commands below including the specific Python version don't matter.

#### Branches

[alpha branch](https://github.com/BingLingGroup/autosub/tree/alpha)

- Include many changes from [the original repo](https://github.com/agermanidis/autosub). Details in [Changelog](CHANGELOG.md). Codes will be updated when an alpha version have been released. It is stabler than the dev branch

[origin branch](https://github.com/BingLingGroup/autosub/tree/origin)

- Include the least changes from [the original repo](https://github.com/agermanidis/autosub) except all new features in the [alpha branch](https://github.com/BingLingGroup/autosub/tree/alpha). The changes in [origin branch](https://github.com/BingLingGroup/autosub/tree/dev) just make sure there's no critical bugs when the program is running on Windows. Currently isn't maintained.

[dev branch](https://github.com/BingLingGroup/autosub/tree/dev)

- The latest codes will be pushed to this branch. If it works fine, it will be merged to alpha branch when new version released.
- Only used to test or pull request. Don't install them unless you know what you are doing.

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

#### Install on Ubuntu

**[ATTENTION]**: Dependencies install commands on the first line.

Install from PyPI.

```bash
apt install ffmpeg python python-pip -y
pip install autosub
```

Install from `origin` branch.

```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@origin
```

Install from `alpha` branch.

```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

#### Install on Windows

You can just go to the [release page](https://github.com/BingLingGroup/autosub/releases) and download the latest release for Windows.

- The one without pyinstaller suffix is built by Nuitka. It's faster than the pyinstaller due to its compiling feature different from pyinstaller which just bundles the application.
- If there's anything wrong on the both releases. You can use the traditional python package installation method below.

Or install python environment(if you still don't have one) from choco and then install the package.

Choco install command for cmd usage.

```batch
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
```

Install from `origin` branch.

```batch
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@origin
```

Install from `alpha` branch.

```batch
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

#### Input

A video or an audio file. Using ffmpeg to convert the format into [the proper format](https://github.com/gillesdemey/google-speech-v2#data).

#### Divide

Since this Speech-to-Text api only accept short-form audio which is not longer than [10 to 15 seconds](https://github.com/gillesdemey/google-speech-v2#caveats), we need to divide one audio file into many small pieces which contain the speech parts.

Use the average power of a small fragment of sound (4096 frames long, 16000 sample rate is about 0.256 seconds) as the instantaneous power as the intensity to find the speech region.

Or uses external regions from the file that pysubs2 supports like `.ass` or `.srt`. This will allow you to manually adjust the regions to get better recognition result.

- [Pre-processing](https://github.com/agermanidis/autosub/issues/40) may be needed to improve the recognition result.

#### Speech-to-Text/Translation API request

Makes parallel requests to generate transcriptions for those regions.

- Post-processing for the subtitle lines may be needed, some of which are too long to hold in a single line at the bottom of the video frame.

(optionally) Translates them to a different language, and finally saves the resulting subtitles to the local storage.

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

#### Speech-to-Text/Translation language support

The Speech-to-Text lang codes are different from the Translation lang codes due to the difference between these two APIs.

To see which, run the utility with the argument `-lsc` or `--list-speech-to-text-codes` and `-ltc` or `--list-translation-codes`. Or just open [constants.py](autosub/constants.py) and check.

- Currently supported lang codes are hard-coded to avoid any inaccurate recognition since if not using the codes on the list but somehow the api accept it, the Google's API recognizes your audio in the ways that depend on your IP address which is uncontrollable by yourself.

#### Output

Currently suppports `.srt`, `.vtt`, `.json`, `.txt`(the same as the Aegisub plain text output).

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### Usage

For the original autosub usage, see[简体中文使用指南](https://binglinggroup.github.io/archives/autosub安装使用指南(windows及ubuntu).html).

For the modified alpha branch version, see the help info below.

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

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>