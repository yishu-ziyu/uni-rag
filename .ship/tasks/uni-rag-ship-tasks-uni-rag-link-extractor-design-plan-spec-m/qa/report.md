# QA Report: Link Extractor Feature

## Interactive Verification

### CLI
- `uni-rag --help` → shows `ingest-url` command ✓
- `uni-rag kb --help` → shows `ingest-url` subcommand ✓
- Both commands display correct help text

### Web UI (HTML inspection)
- `index.html` contains `#url-section` with input field and submit button ✓
- `app.js` contains `submitUrl()` function calling `/api/ingest/url` ✓

### API (via unit/integration tests)
- `POST /api/ingest/url` returns `job_id` and `status_url` ✓
- `POST /api/ingest/url` with empty/invalid URL returns 400 ✓
- Job polling reaches `completed` with `chunks > 0` and `format == "url"` ✓

## Acceptance Criteria Evidence

| AC | Evidence | Status |
|---|---|---|
| AC-1 网页链接提取 | Integration test `test_ingest_url_job_reports_progress` + unit tests | ✓ |
| AC-2 复用 pipeline | E2E test `test_ingest_url_returns_correct_format` + metadata test | ✓ |
| AC-3 Web UI | HTML/JS static check (E2E test) + manual HTML inspection | ✓ |
| AC-4 CLI | E2E test `test_ingest_url_help` + manual `--help` verification | ✓ |
| AC-5 向后兼容 | All existing tests pass (95 tests, no regression) | ✓ |
| AC-6 错误可观测 | E2E test `test_extraction_error_has_hint` + `test_unsupported_platform_message` | ✓ |

## Edge Cases Not Covered by E2E Tests

1. **Real URL extraction with Trafilatura** — not tested (requires network + real URL)
2. **Large document extraction** — not tested (would need a large webpage fixture)
3. **Concurrent URL ingestion** — not tested (multiple simultaneous jobs)
4. **URL with special characters** — not tested (URLs with unicode, query params, fragments)
5. **Progress callback accuracy** — not tested (progress percentages are approximate)
6. **BM25 search after URL ingestion** — not tested (integration test only checks vector store)

## Issues Found

None. The feature works as specified. The three P3 advisory notes from the review are:
- Error message detail level (cosmetic)
- CLI UX (consistent with existing pattern)
- BM25 metadata consistency (same as existing file ingest)

## Recommendation

Feature is ready for merge. P3 items can be addressed in a follow-up PR.
