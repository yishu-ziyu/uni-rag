# Spec: Video Platform Extractors (P8-P9)

## 1. 目标

用户粘贴 YouTube 或 B站视频链接 → 系统自动提取字幕（或 ASR 转写）→ 解析切块 → 向量入库 → 可对话。

**一句话：把"视频"也变成可搜索的文本。**

---

## 2. 现有架构（基线）

P1-P7 已建立：
- `LinkExtractor` ABC + `EXTRACTORS` 注册表
- `WebExtractor` 兜底提取器
- `IngestPipeline.ingest_url()` 复用现有 chunk/embed/index 流程
- `POST /api/ingest/url` API 端点
- Web UI 链接输入框 + CLI `ingest-url` 命令

新增的 `YouTubeExtractor` 和 `BilibiliExtractor` 将插入 `EXTRACTORS` 列表，优先级高于 `WebExtractor`。

---

## 3. 新增架构设计

### 3.1 核心接口：复用 LinkExtractor

```python
class YouTubeExtractor(LinkExtractor):
    """YouTube 字幕提取器。"""
    def can_handle(self, url: str) -> bool:
        return "youtube.com" in url or "youtu.be" in url

    def extract(self, url: str) -> LinkExtractionResult:
        # 1. 检测 yt-dlp 是否存在
        # 2. 尝试提取字幕（--write-subs --write-auto-subs）
        # 3. 无字幕 → 下载音频 → faster-whisper ASR
        # 4. 解析字幕/转写文本 → LinkExtractionResult
```

```python
class BilibiliExtractor(LinkExtractor):
    """B站视频提取器（三层降级）。"""
    def can_handle(self, url: str) -> bool:
        return "bilibili.com" in url or "b23.tv" in url

    def extract(self, url: str) -> LinkExtractionResult:
        # 1. BBDown --sub-only
        # 2. yt-dlp 字幕（备用）
        # 3. 无字幕 → 下载音频 → faster-whisper ASR
```

### 3.2 共享基础设施

#### SubprocessExtractorMixin

```python
class SubprocessExtractorMixin:
    """提供 subprocess 调用的通用方法。"""

    @staticmethod
    def check_executable(name: str) -> bool:
        """检测可执行文件是否在 PATH 中。"""
        return shutil.which(name) is not None

    @staticmethod
    def run_subprocess(cmd: list[str], timeout: int = 120) -> str:
        """运行子进程，返回 stdout。失败时抛出 LinkExtractionError。"""
```

#### SRT 解析

```python
def parse_srt(text: str) -> str:
    """将 SRT 字幕解析为纯文本，去除时间戳和行号。"""
    # 移除时间戳行（如 00:00:01,000 --> 00:00:04,000）
    # 移除空行
    # 合并连续字幕块
    # 返回纯文本
```

#### ASR 回退

```python
def transcribe_audio(audio_path: Path, language: str = "zh") -> str:
    """用 faster-whisper 转写音频为文本。可选依赖。"""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), language=language)
        return " ".join(seg.text for seg in segments)
    except ImportError:
        raise LinkExtractionError("youtube", "blocked", "未安装 faster-whisper，无法转写音频。请运行: pip install faster-whisper")
```

### 3.3 注册表更新

```python
EXTRACTORS: list[LinkExtractor] = [
    YouTubeExtractor(),     # P8
    BilibiliExtractor(),    # P9
    WebExtractor(),         # 兜底
]
```

### 3.4 错误处理

| 错误场景 | reason | hint |
|---|---|---|
| yt-dlp 未安装 | `blocked` | "请先安装 yt-dlp: brew install yt-dlp 或 pip install yt-dlp" |
| BBDown 未安装 | `blocked` | "请先安装 BBDown: https://github.com/nilaoda/BBDown/releases" |
| 视频无字幕 + 无音频 | `no_content` | "该视频没有字幕，且无法提取音频，请尝试其他视频" |
| faster-whisper 未安装 | `blocked` | "请安装 faster-whisper: pip install faster-whisper" |
| ASR 转写失败 | `network` | "音频转写失败，请检查视频是否有有效音频" |
| 平台反爬/封禁 | `blocked` | "平台限制了内容获取，请稍后再试或尝试手动下载字幕后上传" |
| 下载超时 | `timeout` | "视频下载超时，请检查网络后重试" |

### 3.5 Metadata 扩展

```python
metadata = {
    "source": video_title,           # 视频标题
    "format": "url",
    "platform": "youtube",           # 新增: "youtube" | "bilibili"
    "source_url": "https://...",     # 视频链接
    "content_type": "video_subtitle", # 新增
    "duration_seconds": 360,         # 新增: 视频时长
    "subtitle_source": "auto",       # 新增: "manual" | "auto" | "asr"
    "section": "",
    "start": 0,
    "end": 0,
}
```

---

## 4. 技术风险

| 风险 | 等级 | 缓解策略 |
|---|---|---|
| yt-dlp/BBDown 未安装 | 高 | 启动时检测，缺失时返回明确安装指引 |
| faster-whisper 模型下载 | 中 | 首次运行自动下载 base 模型 (~1GB)，网络不好时提示用户 |
| B站 WBI 签名变更 | 中 | BBDown 独立维护，我们只调 CLI |
| 字幕格式多样 | 中 | 统一用 yt-dlp 转 SRT 再解析 |
| 平台反爬/IP 封禁 | 中 | 失败时返回明确错误，不静默跳过 |
| 律师函风险（B站） | 中 | 个人学习工具定位，README 免责声明 |

---

## 5. 实施优先级

```
v0.4 第二批（P8-P9）：
  P8: YouTube 提取器（yt-dlp 字幕 + faster-whisper 兜底）
  P9: B 站提取器（BBDown → yt-dlp → 音频+ASR 三层降级）
```

---

## 6. 文件变更清单

| 操作 | 文件 | 说明 |
|---|---|---|
| **修改** | `src/uni_rag/ingest/link_extractors.py` | 新增 YouTubeExtractor + BilibiliExtractor + 共享工具函数 |
| **修改** | `pyproject.toml` | 新增可选依赖 `faster-whisper` |
| **修改** | `.env.example` | 新增可选配置项（ASR 语言、模型大小） |
| **新建** | `tests/unit/test_video_extractors.py` | YouTube/Bilibili 单元测试（mock subprocess） |

---

## 7. 依赖清单

```toml
[project.optional-dependencies]
video = [
    "faster-whisper>=1.1.0",  # 本地 ASR 回退（可选，~1GB 模型）
]
```

**外部 CLI 工具（需用户自行安装）：**
- `yt-dlp` — `brew install yt-dlp` / `pip install yt-dlp`
- `BBDown` — 从 [BBDown releases](https://github.com/nilaoda/BBDown/releases) 下载

---

## 8. Acceptance Criteria

### AC-1: YouTube 字幕提取
Given 用户粘贴一个 YouTube 视频 URL（有字幕）
When 调用 `extract(url)`
Then 系统必须提取字幕文本，platform="youtube", content_type="video_subtitle"
And 返回的文本必须包含视频标题和字幕内容

### AC-2: YouTube 无字幕回退 ASR
Given 用户粘贴一个 YouTube 视频 URL（无字幕）
When yt-dlp 无法提取字幕
Then 系统必须下载音频并用 faster-whisper 转写
And subtitle_source="asr"

### AC-3: B站 字幕提取（BBDown 优先）
Given 用户粘贴一个 B站视频 URL（有 AI 字幕）
When 调用 `extract(url)`
Then 系统必须通过 BBDown 提取字幕
And platform="bilibili"

### AC-4: B站 三层降级
Given 用户粘贴一个 B站视频 URL
When BBDown 失败
Then 系统必须回退到 yt-dlp
When yt-dlp 也失败
Then 系统必须尝试下载音频 + faster-whisper ASR

### AC-5: 工具缺失时明确提示
Given 用户未安装 yt-dlp
When 调用 `extract(youtube_url)`
Then 必须返回 LinkExtractionError(reason="blocked", hint="请先安装 yt-dlp...")

### AC-6: 注册表优先级
Given YouTubeExtractor 和 BilibiliExtractor 已注册
When 调用 `extract("https://www.youtube.com/watch?v=...")`
Then 必须命中 YouTubeExtractor（不是 WebExtractor）

---

## 9. Golden Journeys

1. **J1 YouTube 字幕问答**：粘贴 YouTube 视频链接 → 提取字幕入库 → 在 Web UI 提问 → 得到带引用的答案
2. **J2 B站 学习**：粘贴 B站视频链接 → BBDown 提取 AI 字幕 → 入库 → 提问视频内容
3. **J3 容错**：粘贴一个无字幕视频 → 收到 `no_content` 或 ASR 转写提示 → 用户理解原因
