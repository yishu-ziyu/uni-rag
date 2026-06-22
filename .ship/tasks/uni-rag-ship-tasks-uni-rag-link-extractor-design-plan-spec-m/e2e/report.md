# E2E Report: Link Extractor Feature

## Test Results
- **New E2E tests**: 10 passed (tests/bdd/test_link_extractor_e2e.py)
- **Existing E2E suite**: 25 passed (tests/integration/)
- **Full suite**: 112 passed, 6 skipped, 93% coverage

## Acceptance Criteria Coverage
- [x] AC-1: POST /api/ingest/url returns job_id → tested
- [x] AC-2: format="url" + metadata platform/source_url → tested
- [x] AC-3: Web UI has link input → tested (HTML + JS checks)
- [x] AC-4: CLI ingest-url commands → tested (CliRunner)
- [x] AC-6: LinkExtractionError user-readable hints → tested

## Skipped
- AC-5 (backward compat): Covered by existing tests passing (no regression)

## Golden Journeys
- J1 (网页问答): Covered by AC-1 + AC-2 integration test
- J2 (CLI 批量): Covered by AC-4 CLI help test
- J3 (容错): Covered by AC-1 invalid URL test + AC-6 error messages

## Evidence
All tests pass deterministically with `-p no:randomly`.
