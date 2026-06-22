# Spec: Link Extractor — 链接即知识

> uni-rag v0.4 功能扩展  
> 状态：设计完成，调研已验证  
> 关联：现有 ingest pipeline (`src/uni_rag/ingest/pipeline.py`)、API routes (`src/uni_rag/api/routes.py`)、Web UI (`src/uni_rag/web/`)

---

## 1. 目标

用户粘贴一个 URL → 系统自动识别平台 → 提取内容 → 解析切块 → 向量入库 → 可对话。

**一句话：把"上传文件"的上游替换为"粘贴链接"。**

---

## 2. 现有架构（基线）

```
文件上传路径（现有）：
  Web UI (file input / drag-drop)
    → POST /api/ingest/jobs
    → RAGPipeline.ingest_file(path, original_name)
    → IngestPipeline.ingest_file()
    → parse_document() → chunk_document() → embed() → vector.add() + bm25.add()
    → 入库完成 → 可查询
```

关键接口：
- `IngestPipeline.ingest_file(path: Path, original_name: str) -> dict`  
  返回 `{"source_id", "chunks", "format", "filename"}`
- `RAGPipeline.ingest_file()` 直接透传到 `IngestPipeline`
- API 用 job 异步模式（`_start_ingest_job` → thread → 轮询 `/api/ingest/jobs/{id}`）

**source_id 计算方式：** `_source_id(path)` 基于文件路径 + 文件前 1MB 内容的 SHA256。URL 提取需要独立的计算逻辑（见 3.3）。

---

## 3. 新增架构设计

### 3.1 核心接口：LinkExtractor

**文件：** `src/uni_rag/ingest/link_extractors.py`（新建）

```python
class LinkExtractionResult:
    """链接提取的标准化输出。"""
    text: str              # 提取的纯文本内容
    title: str             # 标题
    source_url: str        # 原始 URL
    platform: str          # 平台标识：web | youtube | bilibili | wechat | douyin
    content_type: str      # 内容类型：article | video_subtitle | note_text | asr_transcript
    metadata: dict         # 平台特有信息（作者、时长、字幕语言等）

class LinkExtractionError(Exception):
    """链接提取失败。"""
    platform: str
    reason: str            # "unsupported" | "timeout" | "blocked" | "no_content" | "network"
    hint: str              # 给用户的建议
```

```python
class LinkExtractor(ABC):
    """平台内容提取器接口。"""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """判断是否能处理该 URL。"""

    @abstractmethod
    def extract(self, url: str) -> LinkExtractionResult:
        """提取内容。可能耗时（下载音频/字幕），同步阻塞。
        Raises LinkExtractionError on failure.
        """
```

**注册表：** `EXTRACTORS: list[LinkExtractor]`  
按优先级排列，`can_handle()` 依次匹配，第一个命中的处理。

**错误码 → 用户消息映射：**

| 原因码 | 用户消息 |
|---|---|
| `unsupported` | "暂不支持该链接类型，请尝试上传文件或使用其他链接" |
| `timeout` | "内容加载超时，请检查链接是否有效后重试" |
| `blocked` | "平台限制了内容获取，请尝试手动下载后上传" |
| `no_content` | "该链接没有可提取的内容（如无字幕视频），请尝试其他链接" |
| `network` | "网络连接失败，请检查网络后重试" |

### 3.2 各平台提取策略（基于深度调研）

> 调研来源：uni-rag接入优先级评估.md（2026-06-22，4 agent 并行调研）

#### 第一批：立即可做（Week 1-2，低风险）

| 平台 | 工具 | 调用方式 | 难度 | 说明 |
|---|---|---|---|---|
| **通用网页** | **Trafilatura** (v2.1.0, ~4.6k stars, ACL论文, IBM/微软在用) | `pip install trafilatura`，Python API 直接调用 | 低 | 唯一同时满足活跃维护+学术背书+中文可用。`trafilatura.fetch_url()` + `trafilatura.extract()`，5分钟接入。内置语言检测，`target_language='zh'` |
| **YouTube** | **yt-dlp** (stable 2025.10.22, 1700+站点) | `subprocess` 调用 CLI（不走 pip 依赖，独立升级） | 低 | 字幕提取事实标准。`--write-subs --write-auto-subs` 提取手动/自动字幕。无字幕回退 `-x --audio-format mp3` + faster-whisper |

#### 第二批：中文本土平台（Week 3-4，需 Cookie 管理）

| 平台 | 工具 | 调用方式 | 难度 | 说明 |
|---|---|---|---|---|
| **B 站** | **BBDown** (C# CLI，AI字幕/弹幕/字幕SRT最稳定) + **bilibili-api-python** (v17.x) | BBDown 用 subprocess；API 用 pip 包 | 中 | 三层降级：1) BBDown `--sub-only` 提取 AI字幕/上传字幕 2) yt-dlp 字幕 3) 无字幕走音频+ASR。WBI签名2025年5月起强制。注意律师函风险 |
| **微信公众号** | **WechatSogou** (搜狗微信搜索) + 临时链接直接提取 | `pip install wechatsogou` | 中 | 两层配合：WechatSogou 搜文章→拿临时链接→requests+BeautifulSoup提取正文。临时链接有过期时间（通常几天），需立即入库。搜狗接口偶发验证码 |

#### 第三批：按需评估（Week 5+，不建议默认接入）

| 平台 | 评估 |
|---|---|
| **抖音** | 无成熟字幕方案，必须走完整 pipeline：yt-dlp 下载音频 → faster-whisper 转写。短链接时效5-30min、接口加密频繁变动、法律风险最高。仅在用户明确要求且有充足维护资源时接入 |
| **小红书** | **明确跳过**。所有开源方案已基本停滞（2022年后无更新），移动端API多层加密频繁变动，无稳定正文提取实现。标记为"待观察" |

#### 明确跳过的工具

| 工具 | 原因 |
|---|---|
| **Newspaper3k** | 已停止更新（0.2.8），社区 fork 出 Newspaper4k |
| **Goose3** | 低活跃度，中文支持仅停用词过滤，提取质量不如 Trafilatura |
| **readability-lxml** | 维护缓慢，中文页面准确率一般 |
| **bilibili-API-collect** | 2026年1月因律师函永久关停 |
| **小红书全部开源方案** | 停滞+加密变动，不可维护 |

### 3.3 与现有 ingest pipeline 的集成

**关键设计决策：链接提取的结果需要转成"虚拟文档"，复用现有解析、切块、嵌入逻辑。**

```
新增入口：IngestPipeline.ingest_url(url: str, original_name: str | None = None) -> dict

内部流程：
  1. LinkExtractorRegistry.extract(url) → LinkExtractionResult
  2. url_parser.py 将 LinkExtractionResult 包装成 ParsedDocument
     - text: extraction_result.text
     - format: "url"（新增 format 值）
     - source_path: url（仅记录，不用于文件 I/O）
     - pages: None
  3. 复用 chunk_document() 切块
  4. 复用 embedder → vector + bm25 存储
  5. metadata 中记录 platform, source_url, content_type
  6. source_id 用 URL 专用计算：SHA256(url + 文本前 1MB)
```

**修改点最小化：**
- **新建** `url_parser.py` — `LinkExtractionResult → ParsedDocument` 转换
- `pipeline.py` 新增 `ingest_url()` 方法（不修改 `ingest_file()`）
- `IngestPipeline.__init__` 和 `RAGPipeline.__init__` 无需改动
- metadata schema 兼容（现有查询只读 `source`, `format`, `section`, `start`, `end`）

### 3.4 用户交互流程

```
Web UI 变化：

  左侧栏 01 区域新增链接输入框：
  ┌─────────────────────────────────┐
  │ 粘贴链接                         │
  │ [https://...            ]       │
  │ [        提取内容并入库  ]       │
  └─────────────────────────────────┘

  下方保留原有的拖拽上传区域（兼容旧用法）

  两种方式的产物统一显示在文件列表中：
  - 上传文件 → 显示 "paper.pdf · 32 块"
  - 粘贴链接 → 显示 "视频标题 · 18 块"（用标题代替文件名）

  CLI 变化：
  $ uni-rag ingest-url https://bilibili.com/video/BV1xxx
  $ uni-rag ingest ./paper.pdf                # 原有功能不变
  $ uni-rag kb ingest <kb_id> ./paper.pdf     # 原有功能不变
  $ uni-rag kb ingest-url <kb_id> <url>       # 新增
```

### 3.5 API 端点设计

**新增：**
- `POST /api/ingest/url` — 提交链接，返回 job_id（复用已有的异步 job 模式）
- `GET /api/ingest/jobs/{job_id}` — 复用已有的 job 状态查询

**请求体：**
```json
{ "url": "https://www.bilibili.com/video/BV1xxx", "kb_id": "optional" }
```

**返回：** 与文件入库完全一致的 `IngestJobStartResponse`

### 3.6 Metadata 扩展

向量库和 BM25 的 metadata 新增字段：

```python
metadata = {
    "source": title,           # 保持兼容：文件名或链接标题
    "format": "url",           # 新增 "url" 值
    "platform": "bilibili",    # 新增：平台标识
    "source_url": "...",       # 新增：原始链接
    "content_type": "video_subtitle",  # 新增
    "section": c.section_title or "",
    "start": c.start_offset,
    "end": c.end_offset,
}
```

**向后兼容：** 现有查询代码只读取 `source`, `format`, `section`, `start`, `end`，新字段对旧代码透明。

### 3.7 外部工具调用策略

| 工具 | 调用方式 | 理由 |
|---|---|---|
| **yt-dlp** | `subprocess.run()` | yt-dlp 更新极快（每月多次），子进程调用可独立升级 |
| **BBDown** | `subprocess.run()` | C# CLI 工具，无 pip 包 |
| **Trafilatura** | 直接 import | pip 包，API 稳定 |
| **bilibili-api-python** | 直接 import | pip 包，v17.x 活跃 |
| **WechatSogou** | 直接 import | pip 包 |
| **faster-whisper** | 直接 import（可选依赖） | 本地 ASR 回退，模型首次下载 ~1-3GB |

---

## 4. 技术风险

| 风险 | 等级 | 缓解策略 |
|---|---|---|
| 平台反爬导致提取失败 | 高 | 每平台独立降级策略；失败时返回 `LinkExtractionError`，不静默跳过 |
| yt-dlp/BBDown 子进程调用 | 中 | 检测可执行文件是否存在，不存在时给出明确安装指引 |
| 平台 API 变更 | 中 | 每个 extractor 独立封装，变更只影响一个文件 |
| Cookie 管理 | 中 | B站/微信需要 Cookie，建议 v0.5 统一做 cookie 池（当前 MVP 先由用户提供） |
| 法律/封禁风险 | 中 | 个人学习工具定位；README 免责声明；B站/微信降低频率 |

---

## 5. 实施优先级

```
v0.4 第一批（MVP 核心）：
  P1: LinkExtractor 接口 + LinkExtractionResult + LinkExtractionError + 注册表
  P2: 通用网页提取器（Trafilatura）
  P3: 新建 url_parser.py
  P4: pipeline.py 新增 ingest_url() + URL 专用 source_id
  P5: API 端点 POST /api/ingest/url
  P6: Web UI 新增链接输入框
  P7: CLI 新增 ingest-url 子命令

v0.4 第二批（视频平台）：
  P8: YouTube 提取器（yt-dlp 字幕 + faster-whisper 兜底）
  P9: B 站提取器（BBDown 字幕 → yt-dlp 字幕 → 音频+ASR 三层降级）

v0.5（后续扩展）：
  P10: 微信公众号提取器（WechatSogou + 临时链接）
  P11: 抖音（按需，yt-dlp + faster-whisper pipeline）
  ❌ 小红书（跳过，无成熟开源方案）
```

---

## 6. 文件变更清单

| 操作 | 文件 | 说明 |
|---|---|---|
| **新建** | `src/uni_rag/ingest/link_extractors.py` | LinkExtractor 接口 + WebExtractor + YouTubeExtractor + BilibiliExtractor |
| **新建** | `src/uni_rag/ingest/url_parser.py` | LinkExtractionResult → ParsedDocument 转换 |
| **修改** | `src/uni_rag/ingest/pipeline.py` | 新增 `ingest_url()` + URL 专用 source_id |
| **修改** | `src/uni_rag/api/routes.py` | 新增 `/api/ingest/url` 端点 + LinkIngestRequest schema |
| **修改** | `src/uni_rag/web/index.html` | 新增链接输入区域 |
| **修改** | `src/uni_rag/web/app.js` | 新增链接提交逻辑 |
| **修改** | `cli/main.py` | 新增 `ingest-url` 和 `kb ingest-url` 子命令 |
| **修改** | `pyproject.toml` | 新增依赖（trafilatura, faster-whisper 等） |
| **修改** | `.env.example` | 新增可选配置项 |

---

## 7. 依赖清单

```toml
[project.dependencies]
trafilatura>=2.1.0        # 通用网页正文提取
faster-whisper>=1.1.0     # 本地 ASR 回退（可选，视频无字幕时使用）

[project.optional-dependencies]
bilibili = [
    "bilibili-api-python>=17.0",  # B站 API 集成
]
wechat = [
    "wechatsogou>=4.4.0",          # 搜狗微信搜索
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
]
```

**外部 CLI 工具（需用户自行安装）：**
- `yt-dlp` — `brew install yt-dlp` / `pip install yt-dlp`
- `BBDown` — 从 [BBDown releases](https://github.com/nilaoda/BBDown/releases) 下载
