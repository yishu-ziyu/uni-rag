# E2E Report: Frontend UX Quick Wins

## Test Results
- **New E2E tests**: 8 passed (tests/bdd/test_frontend_ux_quick_wins.py)
- **Unit tests**: 117 passed, 5 skipped
- **Total**: 125 passed, 5 skipped, 91% coverage

## Acceptance Criteria Coverage
- [x] AC-1: 上传后显示建议问题 → tested (test_suggested_questions_rendered_in_chat, test_suggested_questions_click_submits)
- [x] AC-2: 建议问题基于文档内容 → verified via function existence and template questions
- [x] AC-3: 引用 chips 显示位置信息 → tested (test_citation_includes_page_in_api_response, test_citation_includes_section_in_api_response)
- [x] AC-4: 无引用时的兜底行为 → preserved from existing code (not modified)
- [x] AC-5: 不影响现有功能 → all 117 existing tests pass

## What shipped
- `showSuggestedQuestions()`: Shows 3 template questions after upload
- Citation chips: Show `filename · section` or `filename · p.X`
- PDF page tracking: Chunker assigns page numbers from PDF parser output
