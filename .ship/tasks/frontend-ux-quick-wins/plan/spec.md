# Spec: Frontend UX Quick Wins

## 1. 目标

改善 uni-rag Web UI 的两个高频交互点：
1. 上传资料后主动给出建议问题，降低首问门槛
2. 引用 chips 显示来源位置信息，方便用户定位原文

## 2. 范围

- 仅前端改动（HTML + JS + CSS）
- 不改后端 API
- 不改现有数据模型

## 3. 功能规格

### 3.1 上传后建议问题

**触发时机**: 文件上传完成或 URL 提取完成后（`indexedFileCount` 增加后）。

**展示位置**: 聊天区（`#chat`），替换空状态或在空状态下方显示。

**建议问题来源**:
- 方案 A（MVP）：根据已上传文档的 chunk 内容，用 LLM 生成 3 个相关问题
- 方案 B（Fallback）：预设通用模板问题（"这篇文章的核心观点是什么？"等）

**交互**: 点击建议问题 → 自动填入提问框 → 触发提交。

### 3.2 引用 chips 位置信息

**当前**: citation chip 显示 `[1] filename`

**改为**: `[1] filename · Section`（如果 section 存在）或 `[1] filename · chunk N`（兜底）

**section 来源**: chunk metadata 中已有的 `section` 字段。

## 4. 技术约束

- 纯前端实现，不新增 API 端点
- 保持现有代码风格
- 响应式布局不变

## 5. Acceptance Criteria

### AC-1: 上传后显示建议问题
Given 用户已上传至少一份资料
When 上传完成（文件入库或 URL 提取完成）
Then 聊天区显示 3 个建议问题按钮
And 点击按钮会自动提交对应问题

### AC-2: 建议问题基于文档内容
Given 建议问题已显示
When 用户点击某个建议问题
Then 提交的问题与当前上传的文档内容相关

### AC-3: 引用 chips 显示位置信息
Given AI 回答包含引用
When 渲染引用 chips
Then 每个 chip 格式为 `[N] filename · section` 或 `[N] filename · chunk N`
And section 信息来自 chunk metadata

### AC-4: 无引用时的兜底行为
Given AI 回答没有可追溯引用
When 渲染回答
Then 显示"这条回答没有可追溯引用，不建议直接采信。"警告
(保持现有行为，不改动)

### AC-5: 不影响现有功能
Given 所有改动完成
When 用户执行上传、提问、引用点击、导出等现有操作
Then 所有现有功能正常工作
