# Dev Context: Link Extractor Feature

## TEST_CMD

```bash
uv run pytest tests/ -p no:randomly --ignore=tests/bdd --cov=src/uni_rag --cov-report=term-missing
```

Result: **95 passed, 5 skipped, 93% coverage** (1179 stmts, 82 miss)

## CODE_CONDUCT

### 新增文件

| 文件 | 职责 |
|---|---|
| `src/uni_rag/ingest/link_extractors.py` | LinkExtractor ABC + LinkExtractionResult + LinkExtractionError + WebExtractor + 注册表 |
| `src/uni_rag/ingest/url_parser.py` | LinkExtractionResult → ParsedDocument 转换 |
| `tests/unit/test_link_extractors.py` | 11 个单元测试（can_handle、extract 失败、注册表） |
| `tests/unit/test_url_parser.py` | 5 个单元测试（字段、标题嵌入、空文本、长标题） |
| `tests/unit/test_pipeline_url.py` | 3 个单元测试（返回 dict、source_id 稳定、不同 URL 不同 ID） |
| `tests/integration/test_api.py` | 新增 2 个集成测试（URL job 完成、无效 URL 400） |

### 修改文件

| 文件 | 改动 |
|---|---|
| `src/uni_rag/ingest/pipeline.py` | 新增 `ingest_url()` 方法 + `_source_id_from_url()` static method |
| `src/uni_rag/rag/pipeline.py` | 新增 `ingest_url()` 透传方法 |
| `src/uni_rag/api/routes.py` | 新增 `LinkIngestRequest` schema + `POST /api/ingest/url` 端点 |
| `src/uni_rag/web/index.html` | 新增链接输入区域 |
| `src/uni_rag/web/app.js` | 新增 `submitUrl()` 函数 |
| `cli/main.py` | 新增 `ingest-url` 和 `kb ingest-url` 子命令 |
| `pyproject.toml` | 新增依赖 `trafilatura>=2.0` |

## Per-Story Pattern References

### P1: 接口定义 (link_extractors.py)
- **模式**：dataclass 用于结果 + ABC 用于接口 + 全局注册表
- **参考**：现有 `parsers.py` 的 `ParsedDocument` dataclass 模式
- **偏离**：注册表用全局 list 而非字典，保持平台优先级有序

### P2: 网页提取器 (link_extractors.py)
- **模式**：错误用异常层次（LinkExtractionError with reason/hint）
- **参考**：现有 `parsers.py` 的错误处理模式
- **依赖**：Trafilatura 直接 import（不用 subprocess）
- **注意**：`fetch_url` 可能超时，catch 所有异常转 LinkExtractionError

### P3: URL 解析 (url_parser.py)
- **模式**：最小转换器，复用现有 ParsedDocument
- **参考**：`parsers.py` 的 parse_document 返回格式
- **偏离**：标题作为第一行嵌入文本（`# {title}\n\n{text}`），确保 chunk 时有章节信息

### P4: Pipeline 集成 (pipeline.py)
- **模式**：新方法 `ingest_url()` 与 `ingest_file()` 对称
- **参考**：`ingest_file()` 的 chunk→embed→index 流程
- **关键决策**：import 用 `from uni_rag.ingest import link_extractors`（模块级访问）而非 `from ... import extract`，确保 monkeypatch 可穿透
- **source_id**：用 URL + 文本前 1MB 的 SHA256，与文件版 SHA256(path + 前1MB) 对称

### P5: API 端点 (routes.py)
- **模式**：复用现有异步 job 模式（_run_ingest_job / _start_ingest_job）
- **参考**：`_run_ingest_job` 的 progress callback 模式
- **偏离**：新建 `_run_url_ingest_job` 而非修改 `_run_ingest_job`，保持单一职责

### P6: Web UI (index.html + app.js)
- **模式**：在现有 upload-section 内新增链接输入区域
- **参考**：现有 `submitUpload()` 函数的 progress 显示逻辑
- **注意**：复用 `waitForIngestJob()` 轮询逻辑，不改动文件上传流程

### P7: CLI (cli/main.py)
- **模式**：新增 `@app.command("ingest-url")` 和 `@kb_app.command("ingest-url")`
- **参考**：现有 `ingest` 和 `kb ingest` 子命令

## Known Issues

1. **pytest-randomly 测试隔离**：随机测试顺序下，URL ingest 的后台线程可能与后续测试的 TestClient 生命周期冲突。建议固定测试顺序或在 CI 中加 `-p no:randomly`。
2. **Trafilatura 依赖**：部分网站可能返回空内容或超时，已处理为 LinkExtractionError。
3. **faster-whisper 可选**：v0.4 不默认安装，YouTube/B 站提取留到 P8/P9。
