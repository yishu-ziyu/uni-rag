# Review: Frontend UX Quick Wins

## Diff Summary
2 commits, 18 files, +624 lines. Scope: 2 UX improvements (T1: suggested questions, T2: citation location info).

## Findings

### No blocking findings

All acceptance criteria have test coverage. The code follows existing patterns.

### Advisory notes (P3)

1. **Suggested questions are static templates** — All 3 questions are hardcoded in `app.js`. Consider generating them via LLM based on document content for better relevance.

2. **Page number tracking only works for PDFs** — `page_number` is populated from `ParsedDocument.pages` which only exists for PDFs. DOCX and Markdown files will have `page=0`. This is fine for MVP but could be extended.

3. **Citation chip page format** — Uses `p.X` format. Consider adding "页" character for Chinese users: `p.3` → `第3页`.

4. **No keyboard shortcut for suggested questions** — Users must click with mouse. Consider adding arrow key navigation.

## Verdict: PASS

Ready for QA.
