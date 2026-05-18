from __future__ import annotations

from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry
from agent.specialists.desktop_agent import DesktopAgent
from services.scholar_service import ScholarService


class ScholarAgent:

    def __init__(
        self,
        desktop_agent: DesktopAgent,
        scholar_service: ScholarService | None = None,
    ) -> None:
        self.desktop_agent = desktop_agent
        self.scholar_service = scholar_service or ScholarService()

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            ToolSpec(
                name="open_google_scholar",
                description="在默认浏览器中打开 Google Scholar 首页。",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                handler=self._open_google_scholar,
                group="scholar",
                owner="scholar_agent",
                risk="low",
            )
        )

        registry.register(
            ToolSpec(
                name="search_google_scholar",
                description="在 Google Scholar 中检索论文关键词，并打开结果页。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要检索的论文关键词。",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=self._search_google_scholar,
                group="scholar",
                owner="scholar_agent",
                risk="low",
            )
        )

    def build_search_url(self, query: str) -> str:
        return self.scholar_service.build_search_url(query)

    def _open_google_scholar(self, arguments: dict[str, Any]) -> dict[str, str]:
        if arguments:
            raise ValueError("open_google_scholar 不需要参数")
        return self.desktop_agent.open_url_direct(self.scholar_service.HOME_URL)

    def _search_google_scholar(self, arguments: dict[str, Any]) -> dict[str, str]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("search_google_scholar 需要非空 query")

        search_url = self.scholar_service.build_search_url(query)
        self.desktop_agent.open_url_direct(search_url)
        return {
            "opened_url": search_url,
            "query": query.strip(),
            "mode": "scholar_search",
        }
