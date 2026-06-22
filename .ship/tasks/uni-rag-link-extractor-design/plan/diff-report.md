# Diff Report: spec.md vs peer-spec.md

## Divergence 1: parse_url_result 的位置

| | Host spec | Peer spec |
|---|---|---|
| 位置 | `parsers.py` 新增 `parse_url_result()` | 新建 `url_parser.py` |
| 理由 | 统一在 parsers 模块管理所有解析逻辑 | parsers.py 只处理文件格式，URL 提取是网络获取，职责不同 |

**Resolution: conceded**  
Peer 的观点正确。`parsers.py` 当前只处理本地文件解析（PDF/DOCX/MD），把 URL 提取结果转成 `ParsedDocument` 虽然结果类型相同，但来源完全不同。新建 `url_parser.py` 更符合单一职责原则。

**Action:** spec.md 更新 — `parse_url_result()` 移到 `url_parser.py`

---

## Divergence 2: source_id 计算

| | Host spec | Peer spec |
|---|---|---|
| 处理 | spec.md 未提及 source_id 计算逻辑 | 需要为 URL 提取新增 `_source_id_from_url()` |
| 理由 | 未深入追踪 `_source_id()` 的实现细节 | `_source_id()` 依赖 `path.read_bytes()`，URL 没有本地文件 |

**Resolution: conceded**  
Peer 的追踪正确。`pipeline.py:49-51` 的 `_source_id()` 确实基于文件路径 + 文件内容前 1MB。URL 提取需要独立的 source_id 计算。

**Action:** spec.md 更新 — 补充 URL 专用 source_id 计算说明

---

## Divergence 3: CLI 入口

| | Host spec | Peer spec |
|---|---|---|
| 设计 | spec.md 只写了 `$ uni-rag ingest <url>` | 新增 `ingest-url` 子命令（与 `ingest` 并列） |
| 理由 | 简洁，用户直觉 | 现有 `ingest` 的 `file: Path` 类型不接受 URL，不能混用 |

**Resolution: conceded**  
Peer 的技术分析正确。现有 CLI 的 `ingest` 命令用 `typer.Argument(..., exists=True)` 强制要求本地文件路径。新建 `ingest-url` 子命令更清晰。

**Action:** spec.md 更新 — CLI 增加 `ingest-url` 子命令

---

## Divergence 4: 错误处理

| | Host spec | Peer spec |
|---|---|---|
| 设计 | spec.md 未定义错误处理 | 需要 `LinkExtractionError` + 错误码 + 用户消息映射 |
| 理由 | 依赖于 job 状态的 `failed` 字段 | 不同类型的失败需要不同的用户提示 |

**Resolution: conceded**  
Peer 的建议合理。链接提取的失败场景比文件解析复杂（反爬、无字幕、平台限制等），结构化错误信息能显著改善用户体验。

**Action:** spec.md 更新 — 补充 `LinkExtractionError` 和错误码映射

---

## 总结

| # | 分歧点 | 结论 | spec.md 需要更新 |
|---|---|---|---|
| 1 | url_parser.py vs parsers.py | conceded — 新建 url_parser.py | ✅ |
| 2 | source_id 计算 | conceded — 补充 URL 专用逻辑 | ✅ |
| 3 | CLI 入口 | conceded — 新增 ingest-url 子命令 | ✅ |
| 4 | 错误处理 | conceded — 补充 LinkExtractionError | ✅ |

所有 4 个分歧点都被 peer 说服，spec.md 需要全面更新。
