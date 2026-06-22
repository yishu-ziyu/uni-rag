# Observe Report: Frontend UX Quick Wins

## Status: Pre-merge observation

PR #2 is open. CI is running (first build for this branch).

## What shipped
- Suggested questions appear after upload (3 template questions)
- Citation chips show `p.X` for PDF pages when section is unavailable
- PDF page tracking in chunker metadata

## Test results
- 153 passed, 6 skipped, 91% coverage

## Known issues (P3 advisory)
1. Suggested questions are static templates — could be LLM-generated
2. Page format uses `p.X` — could add Chinese "页" for local users
3. Page tracking only for PDFs — DOCX/MD always show page=0
