# Problem: Video Platform Content Extraction

## User
大学生 / 研究者，需要将 YouTube 视频、B站视频的内容作为文本入库，以便用 RAG 方式提问学习。

## Task
粘贴一个 YouTube 或 B站视频链接 → 系统提取字幕/文本 → 切块 → 向量入库 → 可对话。

## Obstacle
视频平台的内容不是纯文本，需要：
1. 下载字幕（手动/自动）或音频
2. 无字幕时用 ASR（自动语音识别）转写
3. 处理平台特有的反爬和签名机制（B站 WBI 签名）
4. 外部工具（yt-dlp, BBDown）需要 subprocess 调用，增加复杂度

## Evidence
- spec.md 3.2 节详细调研了各平台提取策略
- P1-P7 已完成通用网页提取（Trafilatura）
- EXTRACTORS 注册表已预留 YouTube/Bilibili 位置
- faster-whisper 已列为可选依赖
