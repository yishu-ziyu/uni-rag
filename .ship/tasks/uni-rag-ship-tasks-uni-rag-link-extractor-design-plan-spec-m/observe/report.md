# Observe Report: Link Extractor Feature

## Status: Pre-merge observation

The PR (#1) is open and CI is green, but it has not been merged yet. No production deployment has occurred. This report records the pre-merge state.

## What was shipped

- URL content extraction via Trafilatura (v0.4 MVP, P1-P7)
- API endpoint: POST /api/ingest/url
- CLI: `uni-rag ingest-url` and `uni-rag kb ingest-url`
- Web UI: link input section in study desk

## CI Status
- Docker build: SUCCESS (linux/amd64 + linux/arm64)
- GitGuardian: SUCCESS
- mergeStateStatus: CLEAN

## Learnings

### What worked
- Module-level import pattern (`from X import Y; Y.method()`) made monkeypatch work correctly in threaded tests
- Existing job async pattern in routes.py was straightforward to extend
- BDD test structure (using IngestPipeline directly with mocks) avoided ChromaDB threading issues

### What was unexpected
- `pytest-randomly` caused test ordering failures when running full suite — the URL test's background thread interacted poorly with other tests' TestClient lifecycle
- Docker multi-platform build (amd64 + arm64) takes 45+ minutes on first run due to QEMU emulation and large model downloads

### What needs improvement
1. **Test isolation**: Background threads in API tests should clean up `_ingest_jobs` entries or use a lock to avoid cross-test contamination
2. **Docker build speed**: Consider building for native platform only in CI, or adding a faster test-only workflow
3. **Web UI testing**: No automated browser test for the link input UI — would benefit from Playwright test

## Constitution check
No CONSTITUTION.md found in project. No principle updates needed.
