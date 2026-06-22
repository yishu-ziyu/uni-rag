# Scope: Video Platform Extractors (P8-P9)

## In scope

### P8: YouTube Extractor
- `YouTubeExtractor(LinkExtractor)` 类
- 使用 yt-dlp CLI 提取字幕（`--write-subs --write-auto-subs --sub-format srt`）
- 无字幕时回退：下载音频 → faster-whisper ASR 转写
- 通过 subprocess 调用 yt-dlp（不 pip install）
- 解析 SRT 字幕为纯文本（去除时间戳、合并连续字幕）
- 返回 `LinkExtractionResult`（platform="youtube", content_type="video_subtitle"）

### P9: Bilibili Extractor
- `BilibiliExtractor(LinkExtractor)` 类
- 三层降级策略：
  1. BBDown `--sub-only` 提取 AI 字幕/上传字幕
  2. yt-dlp 字幕提取（备用）
  3. 无字幕时下载音频 → faster-whisper ASR
- 通过 subprocess 调用 BBDown 和 yt-dlp
- WBI 签名由 BBDown 处理（不自行实现）
- 返回 `LinkExtractionResult`（platform="bilibili", content_type="video_subtitle"）

### 共享基础设施
- `SubprocessExtractorMixin` — subprocess 调用的通用工具方法
- SRT 解析工具函数（`parse_srt` → 纯文本）
- faster-whisper ASR 回退函数（`transcribe_audio`）
- 可执行文件检测（`check_executable`）

### 测试
- 单元测试：mock subprocess 调用，验证降级逻辑
- 集成测试：验证 extractor 注册到 EXTRACTORS 列表
- E2E 测试：验证完整 URL → 入库流程

## Out of scope

- **faster-whisper 模型打包** — 用户需自行下载模型（首次运行自动下载）
- **B站 Cookie 管理** — MVP 不处理登录态，公开视频可用
- **YouTube 字幕语言选择** — 默认取第一个可用字幕轨
- **视频时长限制** — 超长视频（>2h）可能导致内存问题，暂不处理
- **批量导入** — 单链接入库，批量留给后续

## Risks

| 风险 | 等级 | 缓解策略 |
|---|---|---|
| yt-dlp/BBDown 未安装 | 高 | 启动时检测，缺失时返回 `LinkExtractionError(reason="blocked", hint="请先安装 yt-dlp: brew install yt-dlp")` |
| faster-whisper 模型下载失败 | 中 | 可选依赖，缺失时降级为"无字幕"错误 |
| B站 WBI 签名变更 | 中 | BBDown 独立维护，我们只调 CLI |
| 字幕格式多样（SRT/VTT/ASS） | 中 | 统一转换为 SRT 再解析 |
| 平台反爬/IP 封禁 | 中 | 失败时返回明确错误，不重试 |
| 律师函风险（B站） | 中 | 个人学习工具定位，README 免责声明 |

## Open Questions

1. faster-whisper 模型大小（base ~1GB, small ~2GB）— 默认用 base？
2. 字幕合并策略 — 相邻字幕块间隔多少算"连续"？
3. BBDown 输出路径 — 如何获取生成的字幕文件路径？
