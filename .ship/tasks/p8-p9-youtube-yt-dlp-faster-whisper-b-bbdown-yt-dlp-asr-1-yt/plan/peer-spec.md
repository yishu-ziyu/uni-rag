# Peer Spec Evaluation: P8-P9 Video Extractors

## Spec Quality Assessment

### Strengths
1. **Clear fallback strategy** — Three-tier degradation for Bilibili (BBDown → yt-dlp → ASR) is well-defined
2. **Error handling** — Each failure mode has a specific `reason` and `hint` mapped
3. **Reuse existing infrastructure** — Leverages `LinkExtractor` ABC, `EXTRACTORS` registry, and `ingest_url()` pipeline
4. **Optional dependency** — faster-whisper is optional, not forced on all users

### Concerns
1. **subprocess security** — `run_subprocess` takes a list of strings, but URL inputs should be sanitized to prevent injection if URLs come from untrusted sources
2. **SRT parsing robustness** — SRT format has edge cases (empty blocks, overlapping timestamps, encoding issues). The spec assumes well-formed SRT.
3. **faster-whisper model selection** — "base" model is ~1GB. For students on metered connections, this is significant. Should we offer a smaller model or download-on-demand?
4. **BBDown output parsing** — BBDown CLI output format may change between versions. Need to pin a minimum version or parse output loosely.
5. **Audio file cleanup** — Downloaded audio files should be cleaned up after ASR to avoid disk bloat.

### Recommendations
1. Add URL validation in `extract()` before passing to subprocess
2. Add `try/except` around SRT parsing for malformed files
3. Document faster-whisper model sizes and let users choose via env var
4. Add `tempfile.TemporaryDirectory` context manager for audio download
5. Pin minimum BBDown version in documentation

## Verdict: SPEC IS SUFFICIENT

The spec covers all acceptance criteria and provides enough detail for implementation. The concerns above are implementation details that can be addressed during dev.
