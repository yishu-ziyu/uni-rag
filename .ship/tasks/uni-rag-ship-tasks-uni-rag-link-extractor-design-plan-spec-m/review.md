# Review: Link Extractor Feature

## Diff Summary
2 commits, 33 files, +2819 lines. Scope: URL content extraction MVP per spec.

## Findings

### No blocking findings

The implementation matches the spec. All acceptance criteria (AC-1 through AC-6) have test coverage. The code follows existing patterns in the codebase.

### Advisory notes

1. **WebExtractor error message includes raw exception text** (`link_extractors.py:262`)
   The `LinkExtractionError` hint includes the raw exception string which may contain internal details. Consider logging the full exception server-side and returning a generic hint to users.

2. **CLI `ingest-url` global command has no `--kb-id` flag**
   Users must use the `kb ingest-url <kb_id> <url>` subcommand for KB-scoped ingestion. This mirrors the existing `ingest`/`kb ingest` pattern, so it's consistent.

3. **BM25 metadata missing `format` field** (`pipeline.py:383-388`)
   BM25 index entries don't include `format: "url"`. Same pattern as `ingest_file`, but worth noting for future consistency.

## Verdict: PASS

No blocking issues. Ready for QA.
