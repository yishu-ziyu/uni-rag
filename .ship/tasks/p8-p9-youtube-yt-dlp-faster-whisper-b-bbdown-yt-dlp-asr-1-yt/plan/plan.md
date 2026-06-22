# Plan: Video Platform Extractors (P8-P9)

> 基于 `spec.md` 转化为可执行任务。  
> 范围：v0.4 第二批（P8-P9），含单元测试。  
> 每条任务都有可检查的完成条件。

---

## 任务清单

### P8a: 共享基础设施 — SRT 解析 + ASR + subprocess 工具

**文件：** `src/uni_rag/ingest/link_extractors.py`（追加）

**内容：**
- `parse_srt(text: str) -> str` — 解析 SRT 字幕为纯文本
  - 移除时间戳行（`00:00:01,000 --> 00:00:04,000`）
  - 移除行号
  - 合并连续字幕块（间隔 < 2 秒）
- `transcribe_audio(audio_path: Path, language: str = "zh") -> str` — faster-whisper ASR
  - 可选依赖，缺失时抛出 LinkExtractionError with hint
  - 模型名可配置（默认 "base"）
- `SubprocessExtractorMixin` — 提供 `check_executable()` 和 `run_subprocess()`

**测试：** `tests/unit/test_video_extractors.py`
- 测试 `parse_srt` 去除时间戳和行号
- 测试 `parse_srt` 合并连续字幕
- 测试 `transcribe_audio` 在 faster-whisper 缺失时抛出错误
- 测试 `check_executable` 检测 yt-dlp/BBDown

**完成条件：** 单元测试通过

---

### P8b: YouTubeExtractor 实现

**文件：** `src/uni_rag/ingest/link_extractors.py`（追加）

**内容：**
- `YouTubeExtractor(LinkExtractor, SubprocessExtractorMixin)`
  - `can_handle`：匹配 youtube.com / youtu.be URL
  - `extract`：
    1. 检测 yt-dlp
    2. `yt-dlp --write-subs --write-auto-subs --sub-format srt --skip-download <url>`
    3. 解析生成的 SRT 文件
    4. 无字幕 → `-x --audio-format mp3 --audio-quality 0` → faster-whisper
    5. 获取视频标题（`yt-dlp --print title`）
  - 返回 `LinkExtractionResult(platform="youtube", content_type="video_subtitle", metadata={"subtitle_source": "manual"|"auto"|"asr", "duration_seconds": int})`

**测试：** `tests/unit/test_video_extractors.py` 追加
- mock `subprocess.run`，验证 yt-dlp 调用参数
- mock 无字幕场景，验证 ASR 回退
- mock yt-dlp 未安装，验证错误提示

**完成条件：** 单元测试通过

---

### P9a: BilibiliExtractor 实现

**文件：** `src/uni_rag/ingest/link_extractors.py`（追加）

**内容：**
- `BilibiliExtractor(LinkExtractor, SubprocessExtractorMixin)`
  - `can_handle`：匹配 bilibili.com / b23.tv URL
  - `extract`：
    1. 检测 BBDown
    2. **第一层**：`BBDown --sub-only <url>` — 提取 AI 字幕/上传字幕
    3. **第二层**：BBDown 失败 → `yt-dlp --write-subs --sub-format srt <url>`
    4. **第三层**：无字幕 → 下载音频 → faster-whisper
    5. 解析 SRT → 纯文本
    6. 获取视频标题（BBDown 输出或 yt-dlp）
  - 返回 `LinkExtractionResult(platform="bilibili", content_type="video_subtitle", metadata={...})`

**测试：** `tests/unit/test_video_extractors.py` 追加
- mock BBDown 成功场景
- mock BBDown 失败 → yt-dlp 回退
- mock 两层都失败 → ASR 回退
- mock BBDown 未安装，验证错误提示

**完成条件：** 单元测试通过

---

### P9b: 注册表集成

**文件：** `src/uni_rag/ingest/link_extractors.py`

**内容：**
- 更新 `EXTRACTORS` 列表：
  ```python
  EXTRACTORS: list[LinkExtractor] = [
      YouTubeExtractor(),
      BilibiliExtractor(),
      WebExtractor(),  # 兜底
  ]
  ```

**测试：** 验证注册顺序
- `test_registry_priority` — YouTube URL 命中 YouTubeExtractor
- `test_registry_priority` — B站 URL 命中 BilibiliExtractor
- `test_registry_priority` — 普通网页 URL 命中 WebExtractor

**完成条件：** 注册表测试通过

---

### P9c: 可选依赖配置

**文件：** `pyproject.toml` + `.env.example`

**内容：**
- `pyproject.toml` 新增：
  ```toml
  [project.optional-dependencies]
  video = ["faster-whisper>=1.1.0"]
  ```
- `.env.example` 新增：
  ```env
  # ASR 配置（可选，需要 faster-whisper）
  ASR_LANGUAGE=zh
  ASR_MODEL=base
  ```

**完成条件：** `pip install -e ".[video]"` 成功安装 faster-whisper

---

## 执行顺序

```
P8a (基础设施) → P8b (YouTube) → P9a (B站) → P9b (注册表) → P9c (依赖配置)
```

P8a 是前置依赖（P8b/P9a 都需要 SRT 解析和 ASR）。

---

## 测试覆盖目标

| 模块 | 测试文件 | 类型 |
|---|---|---|
| SRT 解析 | `tests/unit/test_video_extractors.py` | 单元 |
| ASR 回退 | `tests/unit/test_video_extractors.py` | 单元 |
| YouTubeExtractor | `tests/unit/test_video_extractors.py` | 单元 |
| BilibiliExtractor | `tests/unit/test_video_extractors.py` | 单元 |
| 注册表优先级 | `tests/unit/test_video_extractors.py` | 单元 |
| 集成（URL 入库） | `tests/integration/test_api.py` 追加 | 集成 |
| E2E（BDD） | `tests/bdd/` 追加 | E2E |
