You must use Skill('ship:dev'). Skip preamble and auth gate.

This is the FIX phase only. Fix ONLY the findings below — nothing else.
Do NOT refactor surrounding code, add features, improve naming, or touch
files not mentioned in the findings. Keep the diff minimal and targeted.
Rerun the repo's test/build commands for changed areas and fix any failures.

Findings:
---
# Review: Link Extractor Feature

## Diff Summary
2 commits, 33 files, +2819 lines. Scope: P1-P7 (MVP) from spec.md.

## Findings

### No P1/P2 findings

The implementation matches the spec. All acceptance criteria (AC-1 through AC-6) have test coverage. The code follows existing patterns in the codebase.

### P3 observations (advisory)

1. **WebExtractor error message leaks exception details** (`link_extractors.py:262`)
   ```python
   raise LinkExtractionError("web", "network", f"网络请求失败: {e}")
   ```
   The raw exception `e` (which may contain URLs, stack traces, or internal paths) is passed to the user. In production, this could leak sensitive information. Consider logging the full exception server-side and returning a generic hint like "网络请求失败，请检查链接有效性后重试".

2. **CLI `ingest-url` command doesn't support `--kb-id` flag**
   The spec shows `uni-rag ingest-url <url>` (global) and `uni-rag kb ingest-url <kb_id> <url>` (KB-scoped). There's no `--kb-id` option on the global command. This is consistent with how `ingest` works (file ingest also uses `kb ingest` subcommand), so this is a minor UX gap rather than a spec violation.

3. **BM25 metadata missing `format` field** (`pipeline.py:383-388`)
   The BM25 index metadata doesn't include `format: "url"`, only `source`, `section`, `platform`, `source_url`. This means BM25-only search results won't indicate the document format. Not a bug (existing `ingest_file` has the same pattern), but worth noting for future consistency.

## Verdict: **PASS**

No P1 or P2 findings. The implementation is complete and correct per spec.
---

spec: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/plan/spec.md
run_state: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m/control/run_state.yaml
task_dir: .ship/tasks/uni-rag-ship-tasks-uni-rag-link-extractor-design-plan-spec-m
Mode: /ship:auto staged workflow fix — no user questions.
