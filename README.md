# Autosub <a href="https://pypi.python.org/pypi/autosub"><img src="https://img.shields.io/pypi/v/autosub.svg"></img></a>

<escape><img src="docs/icon/autosub.png" width="128px"></escape>

[autosub icon](docs/icon/autosub.svg) designed by BingLingGroup.

Software: [inkscape](https://inkscape.org/zh/)

Font: [source-han-serif](https://source.typekit.com/source-han-serif) ([SIL](https://github.com/adobe-fonts/source-han-serif/blob/release/LICENSE.txt))

Color: [Solarized](https://en.wikipedia.org/wiki/Solarized_(color_scheme)#Colors)

### Auto-generated subtitles for any video

Autosub is a utility for automatic speech recognition and subtitle generation. It takes a video or an audio file as input, performs voice activity detection to find speech regions, makes parallel requests to Google Web Speech API to generate transcriptions for those regions, (optionally) translates them to a different language, and finally saves the resulting subtitles to disk. It supports a variety of input and output languages (to see which, run the utility with the argument `--list-languages`) and can currently produce subtitles in either the [SRT format](https://en.wikipedia.org/wiki/SubRip) or simple [JSON](https://en.wikipedia.org/wiki/JSON).

### Installation

**[ATTENTION]**: Except the PyPI version, others include non-original codes not from the original repository.

#### Ubuntu

**[ATTENTION]**: Dependency install commands on the first line.

Install from PyPI
```bash
apt install ffmpeg python python-pip -y
pip install autosub
```

Install from `dev` branch
```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@dev
```

Install from `alpha` branch
```bash
apt install ffmpeg python python-pip git -y
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

#### Windows

You can just go to the [release page](https://github.com/BingLingGroup/autosub/releases) and download the latest release for windows.

**[ATTENTION]**: Current Pre-release for autosub is built by pyinstaller, which means you can feel a little delay when open it but it is normal. A faster version built by nuitka is coming soon.

Or install it from choco.

**[ATTENTION]**: choco install command on the first line

Install from `dev` branch(cmd)
```batch
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@dev
```

Install from `alpha` branch(cmd)
```batch
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
choco install git python2 curl -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install git+https://github.com/BingLingGroup/autosub.git@alpha
```

### Usage

```bash
$ autosub -h
usage: autosub [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT] [-S SRC_LANGUAGE]
               [-D DST_LANGUAGE] [-K API_KEY] [-lf] [-lsc] [-ltc] [-htp]
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
                        Reference:
                        https://cloud.google.com/speech-to-text/docs/languages
  -ltc, --list-translation-codes
                        List all available destination language codes, which
                        mean the translation language codes.
                        [WARNING]: Its name format is different
                        from the source language codes.
                        And it's Google who make that difference not
                        the developers of the autosub. Reference:
                        https://cloud.google.com/translate/docs/languages
  -htp, --http-speech-to-text-api
                        Change the speech-to-text api url into the http one
```

### License

MIT
