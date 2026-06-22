# Plan: Link Extractor — 实施计划

> 基于 `spec.md` 转化为可执行任务。  
> 范围：v0.4 第一阶段（MVP），含单元测试。  
> 每条任务都有可检查的完成条件。

---

## 任务清单

### P1: 定义 LinkExtractionResult、LinkExtractionError 和 LinkExtractor 接口

**文件：** 新建 `src/uni_rag/ingest/link_extractors.py`

**内容：**
- `LinkExtractionResult` dataclass：text, title, source_url, platform, content_type, metadata
- `LinkExtractionError` exception：platform, reason, hint
- `LinkExtractor` ABC：can_handle(url) → bool, extract(url) → LinkExtractionResult
- `EXTRACTORS: list[LinkExtractor]` 全局注册表（空列表，后续平台填充）

**测试：** `tests/unit/test_link_extractors.py`
- 测试 can_handle 匹配逻辑
- 测试 extract 抛出 LinkExtractionError 时携带正确 reason/hint
- 测试 EXTRACTORS 注册表添加/查找

**完成条件：** `uv run pytest tests/unit/test_link_extractors.py` 通过

---

### P2: 实现通用网页提取器

**文件：** `src/uni_rag/ingest/link_extractors.py`（追加）

**内容：**
- `WebExtractor(LinkExtractor)` — 用 `trafilatura` 提取网页正文
  - `can_handle`：接受所有 http/https URL（作为兜底 extractor，放在注册表末尾）
  - `extract`：下载页面 → trafilatura 提取 → 返回 LinkExtractionResult
  - 失败时抛出 `LinkExtractionError(reason="network", hint="...")`
- 提取的文本保留原始换行和段落结构

**依赖：** `pyproject.toml` 新增 `trafilatura`（作为 optional dependency）

**测试：** `tests/unit/test_link_extractors.py` 追加
- 用 HTTPX mock 模拟网页响应，验证正文提取
- 测试网络超时时抛出 LinkExtractionError(reason="timeout")
- 测试空页面时抛出 LinkExtractionError(reason="no_content")

**完成条件：** 单元测试通过；手动测试 `curl` 一个真实网页 URL 能提取正文

---

### P3: 新建 url_parser.py — LinkExtractionResult → ParsedDocument

**文件：** 新建 `src/uni_rag/ingest/url_parser.py`

**内容：**
- `parse_url_result(result: LinkExtractionResult) -> ParsedDocument`
  - text: result.text
  - format: "url"
  - source_path: result.source_url（仅记录，不做文件 I/O）
  - pages: None
- 标题作为第一行嵌入文本（`# {title}\n\n{text}`），确保 chunk 时能保留标题结构

**测试：** `tests/unit/test_url_parser.py`
- 验证输出格式为 "url"
- 验证标题被嵌入文本开头
- 验证空文本处理

**完成条件：** 单元测试通过

---

### P4: pipeline.py 新增 ingest_url() 和 URL 专用 source_id

**文件：** `src/uni_rag/ingest/pipeline.py`

**内容：**
- 新增 `_source_id_from_url(url: str, text: str) -> str`  
  计算 SHA256(url + 文本前 1MB)，返回 16 字符 hex
- 新增 `IngestPipeline.ingest_url(url: str, original_name: str | None = None) -> dict`  
  完整流程：extract → url_parser → chunk → embed → index
  - 调用 `LinkExtractorRegistry.extract(url)`
  - 调用 `parse_url_result()`
  - 复用 `chunk_document()` 和 embed/index 逻辑
  - 返回与 `ingest_file` 一致的 dict 结构
- `RAGPipeline` 新增 `ingest_url()` 透传方法

**测试：** `tests/unit/test_pipeline_url.py`（新建）
- Mock LinkExtractor，验证 ingest_url 完成全流程
- 验证 source_id 同一 URL + 同内容 → 相同 source_id
- 验证返回 dict 包含 source_id, chunks, format="url"

**完成条件：** 单元测试通过；集成测试中 `pipeline.ingest_url("https://example.com")` 能正常入库

---

### P5: API 端点 POST /api/ingest/url

**文件：** `src/uni_rag/api/routes.py`

**内容：**
- 新增 `LinkIngestRequest` schema：url: str, kb_id: str | None = None
- 新增 `POST /api/ingest/url` — 与文件入库同样的异步 job 模式
  - 接收 JSON body `{url, kb_id?}`
  - URL 校验（非空、http/https 协议）
  - 调用 `_start_ingest_job` 的变体，job 内调用 `pipeline.ingest_url()`
  - 返回 `IngestJobStartResponse`
- 错误处理：无效 URL → 400；提取失败 → job failed with error message

**测试：** `tests/integration/test_api.py` 追加
- `POST /api/ingest/url` 返回 job_id
- 轮询 job 状态到 completed
- 无效 URL 返回 400
- mock extractor 失败 → job 进入 failed 状态

**完成条件：** 集成测试通过；`curl` 测试端点可用

---

### P6: Web UI 新增链接输入框

**文件：** `src/uni_rag/web/index.html` + `src/uni_rag/web/app.js`

**内容：**
- `index.html`：在 upload-section 顶部新增链接输入区域
  - 输入框 + "提取内容" 按钮
  - placeholder: "粘贴网页链接、B站视频、YouTube 链接..."
- `app.js`：新增 `submitUrl()` 函数
  - 调用 `POST /api/ingest/url`（JSON body）
  - 复用现有的 `waitForIngestJob()` 轮询逻辑
  - 成功后文件列表显示标题（如 "视频标题 · 18 块"）而非 URL
  - 失败时显示 LinkExtractionError 的 hint 消息

**测试：** 手动测试
- 输入 `https://example.com` → 提取成功 → 出现在文件列表
- 输入无效 URL → 显示错误提示
- 与原有拖拽上传区域并存，互不干扰

**完成条件：** Web UI 中链接输入和文件上传都能正常工作

---

### P7: CLI 新增 ingest-url 子命令

**文件：** `cli/main.py`

**内容：**
- 新增 `@app.command("ingest-url")` — `ingest_url(url: str)`
  - 调用 `RAGPipeline().ingest_url(url)`
  - 输出格式与 `ingest` 命令一致
- 新增 `@kb_app.command("ingest-url")` — `ingest_url_kb(kb_id: str, url: str)`
  - 调用 `RAGPipeline(kb_id=kb_id).ingest_url(url)`

**测试：** `tests/integration/test_cli.py` 追加
- `uni-rag ingest-url https://example.com` 正常输出入库信息
- 无效 URL 显示错误

**完成条件：** CLI 测试通过

---

## 执行顺序

```
P1 → P2 → P3 → P4 → P5 → P6 → P7
```

前 4 个任务是纯后端（接口 + 解析 + pipeline），可以顺序完成。  
P5 依赖 P4（API 调用 pipeline）。  
P6/P7 是接入层，可以并行于 P5 之后。

---

## 依赖新增（pyproject.toml）

```toml
# 主依赖（必选）
trafilatura>=2.0

# 可选依赖（视频平台支持）
yt-dlp>=2024.0
```

---

## 测试覆盖目标

| 模块 | 测试文件 | 类型 |
|---|---|---|
| link_extractors | `tests/unit/test_link_extractors.py` | 单元 |
| url_parser | `tests/unit/test_url_parser.py` | 单元 |
| pipeline (URL) | `tests/unit/test_pipeline_url.py` | 单元 |
| API /ingest/url | `tests/integration/test_api.py` 追加 | 集成 |
| CLI ingest-url | `tests/integration/test_cli.py` 追加 | 集成 |
