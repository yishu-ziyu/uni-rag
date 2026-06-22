# Dev Context: Video Platform Extractors (P8-P9)

## TEST_CMD

```bash
uv run pytest tests/ -p no:randomly --ignore=tests/bdd --cov=src/uni_rag --cov-report=term-missing
```

Result: **117 passed, 5 skipped, 91% coverage** (1304 stmts, 114 miss)

## CODE_CONDUCT

### 新增/修改文件

| 文件 | 改动 |
|---|---|
| `src/uni_rag/ingest/link_extractors.py` | 新增 YouTubeExtractor + BilibiliExtractor + 共享工具函数 |
| `tests/unit/test_video_extractors.py` | 22 个单元测试 |
| `pyproject.toml` | 新增可选依赖 `faster-whisper` |

### Per-Story Pattern References

#### P8a: 共享基础设施 (link_extractors.py)
- **新增**: `SubprocessExtractorMixin` — `check_executable()` + `run_subprocess()`
- **新增**: `parse_srt()` — SRT 字幕解析为纯文本
- **新增**: `transcribe_audio()` — faster-whisper ASR，可选依赖
- **模式**: 静态方法 + 模块级函数，保持无状态

#### P8b: YouTubeExtractor
- **继承**: `LinkExtractor` + `SubprocessExtractorMixin`
- **调用**: `yt-dlp --print %(title)s` → `yt-dlp --write-subs` → fallback `yt-dlp -x` + `transcribe_audio`
- **错误处理**: 每个子步骤都有 try/except，失败时抛 `LinkExtractionError`
- **关键**: subprocess 调用用 `run_subprocess` mixin，统一错误处理

#### P9a: BilibiliExtractor
- **继承**: `LinkExtractor` + `SubprocessExtractorMixin`
- **三层降级**: BBDown → yt-dlp → ASR
- **错误处理**: 每层独立 catch，继续下一层

#### P9b: 注册表
- `EXTRACTORS = [YouTubeExtractor(), BilibiliExtractor(), WebExtractor()]`
- 优先级：视频平台 > 通用网页

## 测试注意

- `faster_whisper` 未安装，用 `patch.dict("sys.modules", {"faster_whisper": mock})` mock
- `transcribe_audio` 在模块内被调用，`patch("uni_rag.ingest.link_extractors.transcribe_audio")` 不生效，需 patch `sys.modules`
- ASR 返回文本需 >= 10 字符（`len(text.strip()) < 10` 检查）
