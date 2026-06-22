# Requirement

## Original Input

在 uni-rag 项目中实现链接内容提取功能。设计文档在 .ship/tasks/uni-rag-link-extractor-design/plan/spec.md，调研报告在 /Users/mahaoxuan/Desktop/AI产品经理/uni-rag接入优先级评估.md。实施第一批 MVP（P1-P7）：通用网页提取器（Trafilatura）+ API端点 + Web UI + CLI。第二批（P8-P9 YouTube/B站）暂不实施，留待后续。关键技术决策：1) yt-dlp/BBDown 用 subprocess 调用 2) Trafilatura 直接 import 3) 小红书明确跳过 4) faster-whisper 作为可选依赖。
