# E2E Report: Video Platform Extractors (P8-P9)

## Test Results
- **New E2E tests**: 11 passed (tests/bdd/test_video_extractors_e2e.py)
- **Unit tests**: 22 passed (tests/unit/test_video_extractors.py)
- **Full suite**: 142 passed, 92% coverage

## Acceptance Criteria Coverage
- [x] AC-1: YouTube 字幕提取 → tested (test_youtube_extracts_with_subtitles)
- [x] AC-2: YouTube 无字幕回退 ASR → tested (test_fallback_to_asr_when_no_subtitles)
- [x] AC-3: B站 字幕提取（BBDown 优先）→ tested (test_bilibili_extracts_with_bbdown)
- [x] AC-4: B站 三层降级 → tested (test_three_tier_fallback_bbdown_ytdlp_asr)
- [x] AC-5: 工具缺失时明确提示 → tested (test_ytdlp_not_installed, test_bbdown_not_installed_falls_back_to_ytdlp)
- [x] AC-6: 注册表优先级 → tested (test_youtube_url_hits_youtube_first, etc.)

## Golden Journeys
- J1 YouTube 字幕问答: Covered by AC-1 + AC-2
- J2 B站 学习: Covered by AC-3 + AC-4
- J3 容错: Covered by AC-5

## Evidence
All tests pass deterministically with `-p no:randomly`.
