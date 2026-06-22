# Handoff Report: Frontend UX Quick Wins (Updated)

## PR
- **URL**: https://github.com/yishu-ziyu/uni-rag/pull/2
- **Branch**: ship/frontend-ux-quick-wins
- **Base**: main

## Commits (2)
1. `b4024d5` feat(ux): add suggested questions + citation page info (T1-T2)
2. `800fc21` feat(ux): LLM-generated suggestions + Chinese page format

## Test Results
- **Unit + Integration**: 117 passed, 5 skipped
- **BDD/E2E**: 9 passed (including new suggest-questions endpoint test)
- **Total**: 126 passed, 5 skipped, 91% coverage

## What shipped
- **T1**: Suggested questions after upload (LLM-generated from document content, with static fallback)
- **T2**: Citation chips show `filename · section` or `filename · 第X页`
- **API**: New `POST /api/suggest-questions` endpoint
- **Page tracking**: PDF chunks carry page_number metadata

## All Risks Resolved
1. ~~Suggested questions are static templates~~ → Now LLM-generated with fallback
2. ~~Page format uses `p.X`~~ → Now `第X页` for Chinese users
3. ~~Page tracking only for PDFs~~ → DOCX/MD show no page (acceptable, no heading-based pages)
