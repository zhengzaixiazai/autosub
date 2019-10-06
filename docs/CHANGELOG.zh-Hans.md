## 更新日志

[English](../CHANGELOG.md)

本项目的所有明显改变将被记录在这个文件里。

本文件的格式将会基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，同时本项目的版本号将遵守[Semantic Versioning](https://semver.org/lang/zh-CN/)。

## 目录

- [[0.5.1-alpha] - 2019-08-02](#051-alpha---2019-08-02)
  - [添加](#添加050-alpha)
  - [改动](#改动050-alpha)
- [[0.5.0-alpha] - 2019-07-27](#050-alpha---2019-07-27)
  - [添加](#添加050-alpha)
  - [改动](#改动050-alpha)
- [[0.4.1-alpha] - 2019-07-11](#041-alpha---2019-07-11)
  - [添加](#添加041-alpha)
  - [改动](#改动041-alpha)
- [[0.4.0-alpha] - 2019-02-17](#040-alpha---2019-02-17)
  - [改动](#改动040-alpha)

点击上箭头以返回目录。

### [0.5.1-alpha] - 2019-08-02

#### 添加(0.5.1-alpha)

- 添加翻译源语言代码自动匹配功能。

#### 改动(0.5.1-alpha)

- 修复方法list_to_googletrans的列表越界bug。[issue #48](https://github.com/BingLingGroup/autosub/issues/48)
- 修复unix subprocess.check_output的兼容性问题。[issue #47](https://github.com/BingLingGroup/autosub/issues/47)
- 修复googletrans全角字符长度过长翻译错误的问题。[issue #49](https://github.com/BingLingGroup/autosub/issues/49)

<escape><a href = "#TOC">&nbsp;↑&nbsp;</a></escape>

### [0.5.0-alpha] - 2019-07-27

#### 添加(0.5.0-alpha)

- 为根据音量自动分句时的分句大小提供外部输入参数控制。[issue #3](https://github.com/BingLingGroup/autosub/issues/3)
- 添加项目元数据文件。[issue #5](https://github.com/BingLingGroup/autosub/issues/5)
- 添加输出文件名检测，以避免覆盖写入。
- 添加新的dev分支用于推送最新的代码。
- 添加多个输出格式(ass, ssa, sub, mpl2, tmp)。[issue #20](https://github.com/BingLingGroup/autosub/issues/20)
- 添加参数用于控制[auditok.StreamTokenizer](https://auditok.readthedocs.io/en/latest/core.html#class-summary)和[energy_threshold](https://auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data)。[issue #30](https://github.com/BingLingGroup/autosub/issues/30)
- 添加覆写参数`-y`用于输出文件覆写并且取消任何运行时暂停。[issue #29](https://github.com/BingLingGroup/autosub/issues/29)
- 添加ass样式文件输入并在输出格式是ass时起作用。[issue #21](https://github.com/BingLingGroup/autosub/issues/21)
- 添加自动分句/自动生成时间轴功能，而不需要调用speech-to-text api。[issue #14](https://github.com/BingLingGroup/autosub/issues/14)
- 添加参数用于控制识别结果[可信度](https://github.com/gillesdemey/google-speech-v2#response)。[issue #6](https://github.com/BingLingGroup/autosub/issues/6)
- 添加参数用于删除在语音转文字后产生的空行。
- 添加来自[googletrans](https://github.com/ssut/py-googletrans)的免费API用于翻译。[issue #25](https://github.com/BingLingGroup/autosub/issues/25)
- 添加双语字幕输出。[issue #16](https://github.com/BingLingGroup/autosub/issues/16)
- 添加多种类型字幕同时输出（指可选时间轴字幕/原语言字幕/目标语言字幕/双语字幕的输出）在使用`--output-files`参数时。
- 添加停止主程序工作的异常。[issue #35](https://github.com/BingLingGroup/autosub/issues/35)
- 添加双语字幕样式输入。[issue #32](https://github.com/BingLingGroup/autosub/issues/32)
- 添加字幕翻译。[issue #38](https://github.com/BingLingGroup/autosub/issues/38)
- 添加自动替换翻译结果中`’`为`'`的功能。
- 添加py-googletrans控制参数。[issue #36](https://github.com/BingLingGroup/autosub/issues/36)
- 添加语言代码支持。（依赖于langcodes包）[issue #34](https://github.com/BingLingGroup/autosub/issues/34)
- 添加ass格式的复杂json文件输出。[issue #39](https://github.com/BingLingGroup/autosub/issues/39)
- 添加音频预处理。[issue #7](https://github.com/BingLingGroup/autosub/issues/7)
- 添加用于控制所有ffmpeg参数的选项。[issue #43](https://github.com/BingLingGroup/autosub/issues/43)
- 添加临时文件保存功能。[issue #22](https://github.com/BingLingGroup/autosub/issues/22)
- 添加仅音频片段输出功能。[issue #44](https://github.com/BingLingGroup/autosub/issues/44)
- 添加检测首行字幕语言的功能(googletrans)。[issue #40](https://github.com/BingLingGroup/autosub/issues/40)
- 添加http, https代理支持。（设置环境变量）[issue #17](https://github.com/BingLingGroup/autosub/issues/17)
- 添加i18n支持。[issue #9](https://github.com/BingLingGroup/autosub/issues/9)
- 添加i18n语言选择功能。[issue #45](https://github.com/BingLingGroup/autosub/issues/45)

#### 改动(0.5.0-alpha)

- [issue #5](https://github.com/BingLingGroup/autosub/issues/5)。
  - 重写帮助信息。
  - 重构argparse命令行参数解析。
  - 重构常量。
- 将原先的dev分支改名为origin分支。
- 将alpha分支当作alpha版本发布的分支。
- 修改文档。
- 改进音频转码步骤来获得更好的音频质量用于处理。现在会从原始文件分别地创建出两个文件。一个是48kHz/16bit/单声道的.wav用于本地分句，一个是44.1kHz/24bit/单声道的.flac用于上传给api进行语音识别。需要指出的是[Google-Speech-v2](https://github.com/gillesdemey/google-speech-v2)上面关于api可以接受的.flac声道数说的有问题，经过我的测试实际上api还是不支持两声道的.flac文件的。[agermanidis/autosub issue #155](https://github.com/agermanidis/autosub/issues/155)
- 修改内部音频处理的时间单位为毫秒。[issue #23](https://github.com/BingLingGroup/autosub/issues/23)
- 修改内部时间轴/分句处理为auditok。[issue #27](https://github.com/BingLingGroup/autosub/issues/27)
- 重构内部函数generate_subtitles为3个独立的部分。[issue #24](https://github.com/BingLingGroup/autosub/issues/24)
- [issue #8](https://github.com/BingLingGroup/autosub/issues/8)
  - 修复python3兼容性问题。
  - 修复Nuitka构建问题（Nuitka更新至0.6.4后解决，环境Anaconda2 python3.5）。
- 重构内部函数api_gen_text为两部分。一个是speech_to_text。另一个是text_translation。[issue #33](https://github.com/BingLingGroup/autosub/issues/33)
- 重构txt输出，现在可以用txt输出时间码。
- 修复vtt输出模块替换所有逗号到句号的问题。
- 重构方法list_to_sub_str。[issue #37](https://github.com/BingLingGroup/autosub/issues/37)

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

### [0.4.1-alpha] - 2019-07-11

#### 添加(0.4.1-alpha)

- 添加https语音转文字api的url，并提供选择参数。[agermanidis/autosub pull request #135](https://github.com/agermanidis/autosub/pull/135)
- 添加外部字幕文件输入以控制语音识别分句。[agermanidis/autosub pull request #159](https://github.com/agermanidis/autosub/pull/159)
- 添加用于打包，发布等事务的脚本。

#### 改动(0.4.1-alpha)

- 修复因不确切的语言代码导致的错误识别结果。[agermanidis/autosub pull request #136](https://github.com/agermanidis/autosub/pull/136)
- 修改文档。

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

### [0.4.0-alpha] - 2019-02-17

#### 改动(0.4.0-alpha)

- 修复多个问题。[agermanidis/autosub pull request #128](https://github.com/agermanidis/autosub/pull/128) by [@iWangJiaxiang](https://github.com/iWangJiaxiang)
  - 修复Windows上ffmpeg依赖不存在问题。
  - 修复无法解析JSON对象导致的异常ValueError未被处理的问题。
  - 修复Windows 10临时文件夹权限被拒绝的问题。[agermanidis/autosub issue #15](https://github.com/agermanidis/autosub/issues/15)
- 修复无法解析JSONDecodeError对象导致的异常ValueError未被处理的问题。[agermanidis/autosub pull request #131](https://github.com/agermanidis/autosub/pull/131) by [@raryelcostasouza](https://github.com/raryelcostasouza)

<escape><a href = "#目录">&nbsp;↑&nbsp;</a></escape>

[Unreleased]: https://github.com/BingLingGroup/autosub/compare/0.5.1-alpha...HEAD
[0.5.1-alpha]: https://github.com/BingLingGroup/autosub/compare/0.5.0-alpha...0.5.1-alpha
[0.5.0-alpha]: https://github.com/BingLingGroup/autosub/compare/0.4.1-alpha...0.5.0-alpha
[0.4.1-alpha]: https://github.com/BingLingGroup/autosub/compare/0.4.0-alpha...0.4.1-alpha
[0.4.0-alpha]: https://github.com/BingLingGroup/autosub/releases/tag/0.4.0-alpha
