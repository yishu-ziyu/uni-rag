# Requirement

## Original Input

第二批 P8-P9：实现 YouTube（yt-dlp 字幕 + faster-whisper 兜底）和 B 站（BBDown → yt-dlp → 音频+ASR 三层降级）提取器。关键技术决策：1) yt-dlp/BBDown 用 subprocess 调用 2) faster-whisper 作为可选依赖 3) B站 WBI 签名由 BBDown 处理
