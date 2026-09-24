# Bilibili Transcript Skill

一键提取 Bilibili 视频字幕/转录文字，支持字幕下载和语音转录双模式。

## 核心功能

**智能字幕获取（三级优先级）**
1. **CC字幕** - 人工上传字幕，准确率最高
2. **AI字幕** - B站AI自动生成，支持9种语言（中/英/日/西/阿/葡/韩/德/法）
3. **语音转录** - 本地Whisper模型转录，无字幕视频也能用

## 特色亮点

🌐 **多语言AI字幕** - 自动检测并下载AI字幕，支持语言优先级自定义（如：优先英文，其次中文）

🎤 **5种Whisper模型** - tiny/base/small/medium/large，带显存需求和预估时间提示

🔑 **Cookie支持** - 自动使用WSL Chromium或Windows Edge登录状态，解锁会员视频字幕

📁 **自动归档** - 转录文件自动保存到 `workspace/Bilibili transcript/` 文件夹

## 使用示例

```bash
# 基础使用（自动检测字幕 → AI字幕 → 语音转录）
./scripts/bilibili_transcript.sh "https://www.bilibili.com/video/BVxxxxx/"

# 指定AI字幕语言优先级（英→中→日）
./scripts/bilibili_transcript.sh -l en,zh,ja "BVxxxxx"

# 指定Whisper模型（不询问）
./scripts/bilibili_transcript.sh -m large "BVxxxxx"

# 快速测试模式
./scripts/bilibili_transcript.sh -m tiny -y "BVxxxxx"
```

## 技术栈

- **yt-dlp** - 视频信息获取与字幕下载
- **Whisper** - 本地语音转录（支持GPU加速）
- **Bilibili AI字幕** - 自动识别 `ai-zh` / `ai-en` 等语言代码

## 输出格式

生成标准TXT文档，包含：
- 视频标题、作者、发布时间、时长
- 转录来源（CC字幕/AI字幕/Whisper模型）
- 完整转录文字（纯文本，去除时间戳）

---
**版本**: 2.8.0  
**作者**: OpenClaw  
**发布**: Clawhub
