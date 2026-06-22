# Peer Spec: Link Extractor — 独立审查

> WARNING: Second spec was self-generated, not independent.  
> 以下是基于对 spec.md 的批判性审查，以"找茬"视角写出的替代方案。

---

## 审查发现：spec.md 中的 4 个问题

### Issue 1: 链接的 source_id 生成方式与文件不同，可能导致同一内容重复索引

spec.md 说 `ingest_url` 复用 `IngestPipeline` 的流程，但 `_source_id()` 的实现是：
```python
def _source_id(self, path: Path) -> str:
    h = hashlib.sha256()
    h.update(str(path.resolve()).encode())
    h.update(path.read_bytes()[:1024 * 1024])
    return h.hexdigest()[:16]
```

这是基于**文件路径 + 文件内容前 1MB** 计算的。对于 URL 提取，没有本地文件，这个逻辑需要改。如果直接用 URL 字符串做 hash，用户粘贴同一个链接两次会得到不同的 source_id（因为提取结果可能变化，如字幕更新），这不是 bug 但是值得考虑的设计点。

**建议：** `ingest_url` 应该有独立的 source_id 计算逻辑，基于 URL 本身 + 提取结果的文本 hash。

### Issue 2: parse_url_result 的位置问题

spec.md 说在 `parsers.py` 里新增 `parse_url_result()`。但这不符合关注点分离——`parsers.py` 目前只处理**文件格式解析**（PDF/DOCX/MD）。URL 提取是**网络获取 + 内容提取**，和文件解析是完全不同的职责。

**建议：** 新建 `src/uni_rag/ingest/url_parser.py`，把 `LinkExtractionResult → ParsedDocument` 的转换放这里。

### Issue 3: 缺少 CLI 入口

spec.md 提到 CLI 变化但只写了 `$ uni-rag ingest https://...`。现有的 CLI `ingest` 命令接受 `Path` 类型参数（`file: Path = typer.Argument(..., exists=True)`），无法直接接收 URL。

**建议：** 两种方案：
- A: CLI 增加 `ingest-url` 子命令（与 `ingest` 并列）
- B: CLI 的 `ingest` 增加 `--url` flag（更简洁但增加复杂度）

推荐方案 A，保持接口清晰。

### Issue 4: 链接提取失败的用户反馈路径不明确

现有文件上传失败时，job 会进入 `failed` 状态，前端显示错误信息。但对于链接提取，失败原因更复杂：
- 平台不支持（"暂不支持该平台"）
- 网络超时（"内容加载超时，请重试"）
- 反爬拦截（"平台限制，无法获取内容"）
- 视频无字幕/音频（"该视频没有可用字幕，且音频提取失败"）

spec.md 没有定义错误分类和对应的用户消息。

**建议：** `LinkExtractionResult` 或 `LinkExtractor` 应该返回结构化的错误信息，而非简单的 `None`。可以考虑：
```python
class LinkExtractionError(Exception):
    platform: str
    reason: str  # "unsupported" | "timeout" | "blocked" | "no_content"
    hint: str    # 给用户的建议
```

---

## 修改后的方案补充

### 补充 A: 文件结构

```
src/uni_rag/ingest/
  ├── parsers.py          # 不变（只处理文件格式）
  ├── link_extractors.py  # LinkExtractor 接口 + 各平台实现
  ├── url_parser.py       # LinkExtractionResult → ParsedDocument 转换
  └── pipeline.py         # 新增 ingest_url()
```

### 补充 B: source_id 计算（URL 专用）

```python
def _source_id_from_url(url: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(url.encode())
    h.update(text[:1024*1024].encode())  # 文本前 1MB
    return h.hexdigest()[:16]
```

这样同一 URL 被提取多次时，如果内容没变，source_id 一致，不会重复入库。

### 补充 C: CLI 增加 `ingest-url` 子命令

```python
@app.command("ingest-url")
def ingest_url(url: str = typer.Argument(...), kb_id: str | None = typer.Option(None, "--kb")):
    """从链接提取内容并入库。"""
```

### 补充 D: 错误处理约定

每种失败场景映射到用户可读的消息：

| 原因码 | 用户消息 |
|---|---|
| `unsupported` | "暂不支持该链接类型，请尝试上传文件或使用其他链接" |
| `timeout` | "内容加载超时，请检查链接是否有效后重试" |
| `blocked` | "平台限制了内容获取，请尝试手动下载后上传" |
| `no_content` | "该链接没有可提取的内容（如无字幕视频），请尝试其他链接" |
| `network` | "网络连接失败，请检查网络后重试" |

---

## 结论

spec.md 的大框架正确，但有以下需要修正：
1. ✅ 核心接口设计合理（LinkExtractor 抽象 + 注册表）
2. ⚠️ 需要修正：`parse_url_result` 不应放在 `parsers.py`，应新建 `url_parser.py`
3. ⚠️ 需要补充：URL 专用 source_id 计算逻辑
4. ⚠️ 需要补充：CLI `ingest-url` 子命令
5. ⚠️ 需要补充：结构化错误处理和用户消息映射
