# Diff Report: P8-P9 Spec vs Original Design

## Original Design Reference
- Source: `.ship/tasks/uni-rag-link-extractor-design/plan/spec.md` (v0.4 full design)
- P8: YouTube extractor (yt-dlp subtitles + faster-whisper fallback)
- P9: Bilibili extractor (BBDown → yt-dlp → audio+ASR three-tier fallback)

## Spec Alignment

### P8: YouTube
| Design Spec | This Spec | Status |
|---|---|---|
| yt-dlp CLI via subprocess | ✅ Implemented in YouTubeExtractor.extract() | Aligned |
| --write-subs --write-auto-subs | ✅ Planned | Aligned |
| No subtitles → -x --audio-format mp3 + faster-whisper | ✅ Planned | Aligned |
| faster-whisper as optional dependency | ✅ `[video]` extra in pyproject.toml | Aligned |
| SRT parsing utility | ✅ `parse_srt()` function | Aligned |
| LinkExtractionResult metadata | ✅ platform, content_type, subtitle_source, duration | Aligned |

### P9: Bilibili
| Design Spec | This Spec | Status |
|---|---|---|
| BBDown CLI via subprocess | ✅ BilibiliExtractor uses BBDown | Aligned |
| Three-tier fallback: BBDown → yt-dlp → ASR | ✅ Explicitly defined | Aligned |
| WBI signature handled by BBDown | ✅ Noted in error handling | Aligned |
| bilibili-api-python as pip package | ❌ Not included | Deferred |
| Legal risk disclaimer | ✅ Noted in risks | Aligned |

## Divergences

### 1. bilibili-api-python not included
**Decision:** Defer to future. BBDown handles subtitle extraction without needing the API package. The API package would be needed for metadata (view count, description), but for subtitle extraction, BBDown + yt-dlp is sufficient.

**Rationale:** Reduces dependency surface. BBDown is the primary tool and it doesn't require bilibili-api-python.

### 2. faster-whisper model selection
**Decision:** Use "base" model by default, configurable via env var.

**Rationale:** Base model (~1GB) balances accuracy and size. Users with more resources can choose "small" or "medium".

### 3. SRT parsing approach
**Decision:** Simple regex-based parsing instead of pysrt/srt library.

**Rationale:** Avoid additional dependency. SRT format is simple enough for regex.

## Missing from Original Design
1. **Audio file cleanup** — Added requirement to clean up temp audio files after ASR
2. **URL sanitization** — Added security consideration for subprocess calls
3. **BBDown version pinning** — Added recommendation to document minimum version

## Conclusion
Spec is complete and aligned with original design. Minor divergences are justified and documented.
