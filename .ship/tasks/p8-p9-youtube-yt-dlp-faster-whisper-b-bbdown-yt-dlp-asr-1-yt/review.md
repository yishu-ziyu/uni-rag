# Review: Video Platform Extractors (P8-P9)

## Diff Summary
1 commit (066defc), +669 lines in `src/uni_rag/ingest/link_extractors.py`, +193 lines in `tests/unit/test_video_extractors.py`, +218 lines in `tests/bdd/test_video_extractors_e2e.py`.

Scope: YouTube (P8) + Bilibili (P9) extractors per spec.md.

## Findings

### No blocking findings

All 6 acceptance criteria have test coverage. Implementation follows existing `LinkExtractor` ABC pattern and `EXTRACTORS` registry convention.

### Advisory notes (P3)

1. **faster-whisper is optional but unversioned** (`link_extractors.py:107`)
   `WhisperModel("base", ...)` hardcodes the model size. Consider making model size configurable (tiny/base/small) via env var or parameter, so users on slower machines can use `tiny`.

2. **Bilibili BBDown title parsing is fragile** (`link_extractors.py:266-269`)
   BBDown `--sub-only` output format may vary. The title extraction assumes stdout contains the title; if BBDown changes output format, title will fall back to URL. Not a bug today, but worth a regression test with actual BBDown output.

3. **No duration metadata** (`link_extractors.py:246,342`)
   `duration_seconds` is hardcoded to 0. yt-dlp can extract this via `--print %(duration)s`. Not required by spec, but useful for UI display.

4. **Subprocess timeout varies** (`link_extractors.py:56,268`)
   YouTube uses default 120s, Bilibili BBDown uses 180s. Consider making timeout configurable per extractor or globally.

## Verdict: PASS

Ready for QA.
