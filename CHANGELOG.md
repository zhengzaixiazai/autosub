## Changelog

[简体中文](docs/CHANGELOG.zh-Hans.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## TOC

- [Unreleased](#unreleased)
- [0.5.4-alpha - 2020-01-31](#054-alpha---2020-01-31)
  - [Added](#added054-alpha)
  - [Changed](#changed054-alpha)
- [0.5.3-alpha - 2019-12-30](#053-alpha---2019-12-30)
  - [Changed](#changed053-alpha)
- [0.5.2-alpha - 2019-11-05](#052-alpha---2019-11-05)
  - [Added](#added052-alpha)
  - [Changed](#changed052-alpha)
- [0.5.1-alpha - 2019-08-02](#051-alpha---2019-08-02)
  - [Added](#added051-alpha)
  - [Changed](#changed051-alpha)
- [0.5.0-alpha - 2019-07-27](#050-alpha---2019-07-27)
  - [Added](#added050-alpha)
  - [Changed](#changed050-alpha)
- [0.4.1-alpha - 2019-07-11](#041-alpha---2019-07-11)
  - [Added](#added041-alpha)
  - [Changed](#changed041-alpha)
- [0.4.0-alpha - 2019-02-17](#040-alpha---2019-02-17)
  - [Changed](#changed040-alpha)

Click up arrow to go back to TOC.

### Unreleased

### [0.5.4-alpha] - 2020-01-31

#### Added(0.5.4-alpha)

- Add basic Google Cloud Speech-to-Text support. [issue #10](https://github.com/BingLingGroup/autosub/issues/10)
- Add more bilingual subtitles formats output support. [issue #72](https://github.com/BingLingGroup/autosub/issues/72)

#### Changed(0.5.4-alpha)

- Fix output format limits when input is a subtitles file.
- Remove gtransv2 support.

### [0.5.3-alpha] - 2019-12-30

#### Changed(0.5.3-alpha)

- Fix excessive transcoding time issue. [pull request #66](https://github.com/BingLingGroup/autosub/pull/66)
- Fix Auditok option issues. [issue #70](https://github.com/BingLingGroup/autosub/issues/70)
- Fix output option issue. [issue #73](https://github.com/BingLingGroup/autosub/issues/73)

### [0.5.2-alpha] - 2019-11-05

#### Added(0.5.2-alpha)

- Add issue templates.

#### Changed(0.5.2-alpha)

- Fix last row of empty translation text missing issue. [issue #62](https://github.com/BingLingGroup/autosub/issues/62)
- Fix executable file detection problem in the current directory.

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### [0.5.1-alpha] - 2019-08-02

#### Added(0.5.1-alpha)

- Add translation source lang code auto match.

#### Changed(0.5.1-alpha)

- Fix method list_to_googletrans index error bug. [issue #48](https://github.com/BingLingGroup/autosub/issues/48)
- Fix unix subprocess.check_output compatibility. [issue #47](https://github.com/BingLingGroup/autosub/issues/47)
- Fix googletrans full-wide chars length too long issue. [issue #49](https://github.com/BingLingGroup/autosub/issues/49)

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### [0.5.0-alpha] - 2019-07-27

#### Added(0.5.0-alpha)

- Add arguments for min and max region size. [issue #3](https://github.com/BingLingGroup/autosub/issues/3)
- Add metadata.py. [issue #5](https://github.com/BingLingGroup/autosub/issues/5)
- Add output file name detection to avoid any file overwritting.
- Add new dev branch for latest dev codes to push.
- Add more output format(ass, ssa, sub, mpl2, tmp). [issue #20](https://github.com/BingLingGroup/autosub/issues/20)
- Add arguments for [auditok.StreamTokenizer](https://auditok.readthedocs.io/en/latest/core.html#class-summary) and [energy_threshold](https://auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data). [issue #30](https://github.com/BingLingGroup/autosub/issues/30)
- Add overwrite option `-y` for output overwrite and no input pause. [issue #29](https://github.com/BingLingGroup/autosub/issues/29)
- Add specific .ass style when output format is .ass. [issue #21](https://github.com/BingLingGroup/autosub/issues/21)
- Add timings generating function instead of using speech-to-text api. [issue #14](https://github.com/BingLingGroup/autosub/issues/14)
- Add arguments for [confidence](https://github.com/gillesdemey/google-speech-v2#response) control. [issue #6](https://github.com/BingLingGroup/autosub/issues/6)
- Add arguments for dropping empty lines from speech-to-text results.
- Add free api to use by importing the [googletrans](https://github.com/ssut/py-googletrans). [issue #25](https://github.com/BingLingGroup/autosub/issues/25)
- Add bilingual subtitle output. [issue #16](https://github.com/BingLingGroup/autosub/issues/16)
- Add multi-types subtitles files output at the same time (regions/source language/destination language/bilingual subtitles) when using `--output-files` option.
- Add exception to stop the workflow in main(). [issue #35](https://github.com/BingLingGroup/autosub/issues/35)
- Add bilingual subtitle styles input. [issue #32](https://github.com/BingLingGroup/autosub/issues/32)
- Add subtitles translate. [issue #38](https://github.com/BingLingGroup/autosub/issues/38)
- Add function to auto-replace `’` to `'` in the translation result.
- Add py-googletrans control args. [issue #36](https://github.com/BingLingGroup/autosub/issues/36)
- Add lang codes support.(Depend on langcodes package) [issue #34](https://github.com/BingLingGroup/autosub/issues/34)
- Add complex ass json output. [issue #39](https://github.com/BingLingGroup/autosub/issues/39)
- Add audio preprocessing. [issue #7](https://github.com/BingLingGroup/autosub/issues/7)
- Add options to control every ffmpeg command. [issue #43](https://github.com/BingLingGroup/autosub/issues/43)
- Add temp file save function. [issue #22](https://github.com/BingLingGroup/autosub/issues/22)
- Add only audio fragments output. [issue #44](https://github.com/BingLingGroup/autosub/issues/44)
- Add subtitles(first line) language detection powered by googletrans. [issue #40](https://github.com/BingLingGroup/autosub/issues/40)
- Add http, https proxy support.(Set environment variables) [issue #17](https://github.com/BingLingGroup/autosub/issues/17)
- Add i18n support. [issue #9](https://github.com/BingLingGroup/autosub/issues/9)
- Add i18n language choice. [issue #45](https://github.com/BingLingGroup/autosub/issues/45)

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

#### Changed(0.5.0-alpha)

- [issue #5](https://github.com/BingLingGroup/autosub/issues/5).
  - Rewrite help messages.
  - Refactor argparse.
  - Refactor constaints.
- Change dev branch into origin branch.
- Use alpha branch for alpha releases.
- Change docs.
- Change audio conversion workflow to get a better audio quality to process. Currently will create two files from the original source file separately. 48kHz/16bit/mono .wav for local speech regions finding. 44.1kHz/24bit/mono .flac for google speech v2 api upload or in other words, speech recognition. Need to point out that [Google-Speech-v2](https://github.com/gillesdemey/google-speech-v2) is wrong on the supported .flac audio channel number. According to my test the api doesn't support the 2-channel .flac file. [agermanidis/autosub issue #155](https://github.com/agermanidis/autosub/issues/155)
- Refactor internal regions unit to millisecond. [issue #23](https://github.com/BingLingGroup/autosub/issues/23)
- Refactor speech regions detection by using auditok. [issue #27](https://github.com/BingLingGroup/autosub/issues/27)
- Refactor generate_subtitles into 3 parts. [issue #24](https://github.com/BingLingGroup/autosub/issues/24)
- [issue #8](https://github.com/BingLingGroup/autosub/issues/8)
  - Fix python3 compatibility issues.
  - Fix Nuitka build after updating Nuitka to 0.6.4(Environment Anaconda2 python3.5).
- Refactor api_gen_text to 2 parts. One is speech_to_text. Another is text_translation. [issue #33](https://github.com/BingLingGroup/autosub/issues/33)
- Refactor txt output. Now txt can output regions.
- Fix vtt output replacing all commas to dots issues.
- Refactor list_to_sub_str. [issue #37](https://github.com/BingLingGroup/autosub/issues/37)

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### [0.4.1-alpha] - 2019-07-11

[0.4.1-alpha release](https://github.com/BingLingGroup/autosub/releases/tag/0.4.1-alpha)

#### Added(0.4.1-alpha)

- Add https speech-to-text api url and url choice argument. [agermanidis/autosub pull request #135](https://github.com/agermanidis/autosub/pull/135)
- Add external speech-to-text regions control from external subtitle files. [agermanidis/autosub pull request #159](https://github.com/agermanidis/autosub/pull/159)
- Add scripts to build, release and etc.

#### Changed(0.4.1-alpha)

- Fix vague language codes caused wrong recognition result. [agermanidis/autosub pull request #136](https://github.com/agermanidis/autosub/pull/136)
- Change docs.

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### [0.4.0-alpha] - 2019-02-17

[0.4.0-alpha release](https://github.com/BingLingGroup/autosub/releases/tag/0.4.0-alpha)

#### Changed(0.4.0-alpha)

- Fix several issues. [agermanidis/autosub pull request #128](https://github.com/agermanidis/autosub/pull/128) by [@iWangJiaxiang](https://github.com/iWangJiaxiang)
  - Fix "ffmpeg.exe" causes "Dependency not found: ffmpeg" on Windows.
  - Fix "ValueError" when the response data of "SpeechRecognizer" couldn't be parsed to JSON Object.
  - Fix Temp Folder Permissions Denied on Windows 10. [agermanidis/autosub issue #15](https://github.com/agermanidis/autosub/issues/15)
- Fix JSONDecodeError caused crash. [agermanidis/autosub pull request #131](https://github.com/agermanidis/autosub/pull/131) by [@raryelcostasouza](https://github.com/raryelcostasouza)

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

[Unreleased]: https://github.com/BingLingGroup/autosub/compare/0.5.4-alpha...HEAD
[0.5.4-alpha]: https://github.com/BingLingGroup/autosub/compare/0.5.3-alpha...0.5.4-alpha
[0.5.3-alpha]: https://github.com/BingLingGroup/autosub/compare/0.5.2-alpha...0.5.3-alpha
[0.5.2-alpha]: https://github.com/BingLingGroup/autosub/compare/0.5.1-alpha...0.5.2-alpha
[0.5.1-alpha]: https://github.com/BingLingGroup/autosub/compare/0.5.0-alpha...0.5.1-alpha
[0.5.0-alpha]: https://github.com/BingLingGroup/autosub/compare/0.4.1-alpha...0.5.0-alpha
[0.4.1-alpha]: https://github.com/BingLingGroup/autosub/compare/0.4.0-alpha...0.4.1-alpha
[0.4.0-alpha]: https://github.com/BingLingGroup/autosub/releases/tag/0.4.0-alpha
