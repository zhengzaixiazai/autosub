## 更新日志

[English](../CHANGELOG.md)

本项目的所有明显改变将被记录在这个文件里。

本文件的格式将会基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，同时本项目的版本号将遵守[Semantic Versioning](https://semver.org/lang/zh-CN/)。

## 目录

- [未发布的部分](#未发布的部分)
  - [添加](#添加未发布的部分)
  - [改动](#改动未发布的部分)
- [[0.4.1-alpha] - 2019-07-11](#041-alpha---2019-07-11)
  - [添加](#添加041-alpha)
  - [改动](#改动041-alpha)
- [[0.4.0-alpha] - 2019-02-17](#040-alpha---2019-02-17)
  - [改动](#改动040-alpha)

点击上箭头以返回目录。

### [未发布的部分]

#### 添加(未发布的部分)

- 为根据音量自动分句时的分句大小提供外部输入参数控制。[issue #3](https://github.com/BingLingGroup/autosub/issues/3)
- 添加项目元数据文件。[issue #5](https://github.com/BingLingGroup/autosub/issues/5)
- 添加输出文件名检测，以避免覆盖写入。
- 添加新的dev分支用于推送最新的代码。
- 添加多个输出格式(ass, ssa, sub, mpl2, tmp)。[issue #20](https://github.com/BingLingGroup/autosub/issues/20)

#### 修改(未发布的部分)

- [issue #5](https://github.com/BingLingGroup/autosub/issues/5)。
  - 重写帮助信息。
  - 重构argparse命令行参数解析。
  - 重构常量。
- 将原先的dev分支改名为origin分支。
- 将alpha分支当作alpha版本发布的分支。
- 修改文档。
- 改进音频转码步骤来获得更好的音频质量用于处理。现在会从原始文件分别地创建出两个文件。一个是48kHz/16bit/单声道的.wav用于本地分句，一个是44.1kHz/24bit/单声道的.flac用于上传给api进行语音识别。需要指出的是[Google-Speech-v2](https://github.com/gillesdemey/google-speech-v2)上面关于api可以接受的.flac声道数说的有问题，经过我的测试实际上api还是不支持两声道的.flac文件的。[agermanidis/autosub issue #155](https://github.com/agermanidis/autosub/issues/155)
- 修改内部音频处理的时间单位为毫秒。[issue #23](https://github.com/BingLingGroup/autosub/issues/23)

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
