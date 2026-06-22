# Refactor Report
## Changes Made
No refactoring needed — the implementation was already clean.

## Why no changes were needed
- `link_extractors.py`: Follows the established `LinkExtractor` ABC pattern correctly
  - `SubprocessExtractorMixin` properly encapsulates subprocess logic
  - `parse_srt()` and `transcribe_audio()` are well-scoped utilities
  - Error handling maps to `LinkExtractionError` consistently
- `YouTubeExtractor` and `BilibiliExtractor`: Follow the same structure as `WebExtractor`
- Registry (`EXTRACTORS`): Correctly ordered by priority

## Advisory (from review)
4 P3 notes recorded in `review.md` — none require code changes for MVP.
