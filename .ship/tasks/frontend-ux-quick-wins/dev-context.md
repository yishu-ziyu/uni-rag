# Dev Context: Frontend UX Quick Wins
## TEST_CMD

```bash
uv run pytest tests/ -p no:randomly --ignore=tests/bdd --cov=src/uni_rag --cov-report=term-missing
```

Result: **117 passed, 5 skipped, 91% coverage** (1333 stmts, 121 miss)

## Changes Summary

### T2: Citation chips with location info
- `chunker.py`: Added `page_number` field to `Chunk` dataclass
- `chunker.py`: `chunk_document()` accepts optional `pages` parameter for PDF page tracking
- `pipeline.py`: Passes `pages` to chunker for both file and URL ingest
- `pipeline.py`: Stores `page` in vector + BM25 metadata
- `rag/pipeline.py`: `_extract_citations()` includes `page` in output
- `api/schemas.py`: `Citation` model includes `page` field
- `web/app.js`: Citation chip renders `p.X` when section is empty

### T1: Suggested questions after upload
- `web/app.js`: Added `showSuggestedQuestions()` function
- `web/app.js`: Called after file upload and URL ingest completion
- `web/style.css`: Added `.suggested-questions` + `.suggest-chip` styles

### Files changed
- `src/uni_rag/ingest/chunker.py` (+34 lines)
- `src/uni_rag/ingest/pipeline.py` (+9/-6 lines)
- `src/uni_rag/rag/pipeline.py` (+3 lines)
- `src/uni_rag/api/schemas.py` (+1 line)
- `src/uni_rag/web/app.js` (+44 lines)
- `src/uni_rag/web/style.css` (+35 lines)
- `tests/bdd/test_frontend_ux_quick_wins.py` (+144 lines, 8 tests)

## Manual Verification
1. Upload a PDF → see 3 suggested question buttons below file list
2. Click a suggested question → it submits automatically
3. Ask a question → citation chips show `filename · section` or `filename · p.X`
