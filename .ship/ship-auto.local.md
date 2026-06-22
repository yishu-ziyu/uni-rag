---
active: true
task_id: uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
session_id: c8c704aa-7eb5-415f-990a-0aab40c6c808
branch: ship/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
phase: refactor
scope_mode: full
review_fix_round: 0
qa_fix_round: 0
e2e_fix_round: 0
post_qa_fix: false
started_at: "2026-06-22T07:30:27Z"
pre_dev_sha: 2d64ee5977db0e15dec389e2d64596cfc9c284d1
pre_refactor_sha: b4e1da04ff005a0b8c1638b2b7ff4d33902a88ff
---

在 uni-rag 项目中实现链接内容提取功能。设计文档在 .ship/tasks/uni-rag-link-extractor-design/plan/spec.md，调研报告在 /Users/mahaoxuan/Desktop/AI产品经理/uni-rag接入优先级评估.md。实施第一批 MVP（P1-P7）：通用网页提取器（Trafilatura）+ API端点 + Web UI + CLI。第二批（P8-P9 YouTube/B站）暂不实施，留待后续。关键技术决策：1) yt-dlp/BBDown 用 subprocess 调用 2) Trafilatura 直接 import 3) 小红书明确跳过 4) faster-whisper 作为可选依赖。
