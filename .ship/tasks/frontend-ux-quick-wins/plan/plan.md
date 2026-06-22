# Plan: Frontend UX Quick Wins

## 任务清单

### T1: 实现建议问题生成
- [ ] 新建 `src/uni_rag/web/suggestions.js`：负责生成和渲染建议问题
- [ ] 在 `app.js` 中接入：上传完成后调用 `showSuggestions()`
- [ ] 建议问题来源：先用 LLM 生成（复用现有 pipeline），fallback 到模板
- [ ] 点击建议问题 → 填入输入框 → 自动提交

### T2: 引用 chips 加位置信息
- [ ] 修改 `renderMessage()` 中的 citation chip 渲染逻辑
- [ ] 格式：`[N] filename · section`（section 存在时）或 `[N] filename`
- [ ] 从 citation metadata 读取 section 字段

### T3: 样式调整
- [ ] 建议问题按钮样式（`.suggested-questions` + `.suggest-chip`）
- [ ] citation chip 位置信息样式（`.cite-location`）

### T4: 测试
- [ ] 手动验证：上传文件 → 看建议问题 → 点击提交
- [ ] 手动验证：提问 → 看引用 chips 是否有 section 信息
- [ ] 回归验证：现有上传/提问/引用功能正常

## 实施顺序
1. T2（引用 chips）— 简单，立即可见
2. T1（建议问题）— 需要接入 LLM，稍复杂
3. T3（样式）— 随 T1/T2 一起
4. T4（验证）— 最后
