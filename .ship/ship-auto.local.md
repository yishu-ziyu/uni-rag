---
active: true
task_id: p8-p9-youtube-yt-dlp-faster-whisper-b-bbdown-yt-dlp-asr-1-yt
session_id: c8c704aa-7eb5-415f-990a-0aab40c6c808
branch: ship/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
phase: review
scope_mode: full
review_fix_round: 0
qa_fix_round: 0
e2e_fix_round: 0
post_qa_fix: false
started_at: "2026-06-22T11:39:23Z"
pre_dev_sha: 715fcdf35c5b71861ca8bfedaa9df6310cae28f8
---

第二批 P8-P9：实现 YouTube（yt-dlp 字幕 + faster-whisper 兜底）和 B 站（BBDown → yt-dlp → 音频+ASR 三层降级）提取器。关键技术决策：1) yt-dlp/BBDown 用 subprocess 调用 2) faster-whisper 作为可选依赖 3) B站 WBI 签名由 BBDown 处理
