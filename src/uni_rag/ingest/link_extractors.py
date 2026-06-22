"""Link extractors: platform-specific content extraction from URLs."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import httpx
import trafilatura


@dataclass
class LinkExtractionResult:
    """标准化链接提取输出。"""
    text: str
    title: str
    source_url: str
    platform: str = "web"
    content_type: str = "article"
    metadata: dict[str, Any] = field(default_factory=dict)


class LinkExtractionError(Exception):
    """链接提取失败。"""
    def __init__(self, platform: str, reason: str, hint: str):
        self.platform = platform
        self.reason = reason
        self.hint = hint
        super().__init__(f"[{platform}] {reason}: {hint}")


class LinkExtractor(ABC):
    """平台内容提取器接口。"""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """判断是否能处理该 URL。"""

    @abstractmethod
    def extract(self, url: str) -> LinkExtractionResult:
        """提取内容。同步阻塞，可能耗时。Raises LinkExtractionError on failure."""


class WebExtractor(LinkExtractor):
    """通用网页正文提取（Trafilatura）。兜底 extractor，接受所有 http/https URL。"""

    TIMEOUT = 15.0

    def can_handle(self, url: str) -> bool:
        return url.startswith(("http://", "https://"))

    def extract(self, url: str) -> LinkExtractionResult:
        try:
            downloaded = httpx.get(url, timeout=self.TIMEOUT)
        except Exception as e:
            raise LinkExtractionError("web", "network", f"网络请求失败: {e}") from e

        if not downloaded:
            raise LinkExtractionError("web", "network", "无法获取页面内容，请检查链接是否有效")

        try:
            text = trafilatura.extract(
                downloaded,
                include_title=True,
                include_links=False,
                include_images=False,
                target_language="zh",
                no_fallback=False,
            )
        except Exception as e:
            raise LinkExtractionError("web", "network", f"内容解析失败: {e}") from e

        if not text or len(text.strip()) < 20:
            raise LinkExtractionError("web", "no_content", "页面未提取到有效正文内容")

        # 用第一行作为标题
        lines = text.strip().split("\n", 1)
        title = lines[0].strip() if lines else url
        if len(title) > 80:
            title = title[:77] + "..."
        body = lines[1].strip() if len(lines) > 1 else text

        return LinkExtractionResult(
            text=body,
            title=title,
            source_url=url,
            platform="web",
            content_type="article",
            metadata={},
        )


# 全局注册表，按优先级排列
EXTRACTORS: list[LinkExtractor] = [
    # YouTube, Bilibili 等后续平台 extractor 插在这里（优先级高于 WebExtractor）
    WebExtractor(),  # 兜底，放最后
]


def extract(url: str) -> LinkExtractionResult:
    """遍历注册表，找到第一个能处理该 URL 的 extractor 并执行。"""
    for extractor in EXTRACTORS:
        if extractor.can_handle(url):
            return extractor.extract(url)
    raise LinkExtractionError("unknown", "unsupported", "暂不支持该链接类型，请尝试上传文件或使用其他链接")
