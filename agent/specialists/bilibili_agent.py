from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

from agent.models import ToolSpec
from agent.registry import ToolRegistry
from agent.specialists.desktop_agent import DesktopAgent
from services.bilibili_service import BilibiliService


class BilibiliAgent:
    """负责把 B 站领域请求翻译成可执行网页动作的专长 Agent。"""

    MEDIA_ID_PATTERN = re.compile(r"/medialist/play/(?P<media_id>\d+)")

    def __init__(
        self,
        desktop_agent: DesktopAgent,
        bilibili_service: BilibiliService | None = None,
    ) -> None:
        self.desktop_agent = desktop_agent
        self.bilibili_service = bilibili_service or BilibiliService()

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            ToolSpec(
                name="play_bilibili_favorite_folder",
                description=(
                    "打开 B 站收藏夹播放页。需要用户提供收藏夹链接，"
                    "或直接提供收藏夹 media_id。"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "favorite_url": {
                            "type": "string",
                            "description": "B 站收藏夹链接，可选。",
                        },
                        "media_id": {
                            "type": "string",
                            "description": "B 站收藏夹 media_id，可选。",
                        },
                    },
                    "additionalProperties": False,
                },
                handler=self._play_favorite_folder,
                group="bilibili",
                owner="bilibili_agent",
                risk="low",
            )
        )

        registry.register(
            ToolSpec(
                name="search_bilibili_and_open_first_video",
                description="在 B 站按关键词搜索，并打开搜索结果中的第一个普通视频。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要搜索的视频关键词。",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=self._search_and_open_first_video,
                group="bilibili",
                owner="bilibili_agent",
                risk="low",
            )
        )

    def _play_favorite_folder(self, arguments: dict[str, Any]) -> dict[str, str]:
        media_id = self._extract_media_id(arguments)
        if media_id is None:
            raise ValueError("需要 favorite_url 或 media_id 才能打开收藏夹播放页")

        playback_url = f"https://www.bilibili.com/medialist/play/{media_id}"
        self.desktop_agent.open_url_direct(playback_url)
        return {
            "opened_url": playback_url,
            "mode": "favorite_folder_playlist",
        }

    def _search_and_open_first_video(self, arguments: dict[str, Any]) -> dict[str, str]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("search_bilibili_and_open_first_video 需要非空 query")

        first_video = self.bilibili_service.search_first_video(query)
        self.desktop_agent.open_url_direct(first_video.url)
        return {
            "opened_url": first_video.url,
            "title": first_video.title,
            "bvid": first_video.bvid,
            "mode": "search_first_video",
        }

    def build_search_url(self, query: str) -> str:
        return f"https://search.bilibili.com/video?keyword={quote_plus(query.strip())}"

    def _extract_media_id(self, arguments: dict[str, Any]) -> str | None:
        media_id = arguments.get("media_id")
        if isinstance(media_id, str) and media_id.strip():
            return media_id.strip()

        favorite_url = arguments.get("favorite_url")
        if not isinstance(favorite_url, str) or not favorite_url.strip():
            return None

        parsed = urlparse(favorite_url)
        path_match = self.MEDIA_ID_PATTERN.search(parsed.path)
        if path_match:
            return path_match.group("media_id")

        query = parse_qs(parsed.query)
        for key in ("media_id", "fid"):
            values = query.get(key)
            if values and values[0].strip():
                return values[0].strip()

        return None
