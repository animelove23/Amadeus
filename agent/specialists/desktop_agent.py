from __future__ import annotations

from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry
from services.desktop_service import DesktopService


class DesktopAgent:
    """负责打开网页与桌面项目的专长 Agent。"""

    def __init__(self, desktop_service: DesktopService | None = None) -> None:
        self.desktop_service = desktop_service or DesktopService()

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            ToolSpec(
                name="open_google",
                description="在默认浏览器中打开 Google。",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                handler=self._open_google,
                group="desktop",
                owner="desktop_agent",
                risk="low",
            )
        )

        registry.register(
            ToolSpec(
                name="open_url",
                description="在默认浏览器中打开一个 http 或 https 网页。",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要打开的网址。",
                        }
                    },
                    "required": ["url"],
                    "additionalProperties": False,
                },
                handler=self._open_url,
                group="desktop",
                owner="desktop_agent",
                risk="low",
            )
        )

        registry.register(
            ToolSpec(
                name="open_desktop_item",
                description="按准确名称打开用户桌面上的文件、文件夹或快捷方式。",
                parameters={
                    "type": "object",
                    "properties": {
                        "item_name": {
                            "type": "string",
                            "description": "桌面项目的准确文件名，例如 Chrome.lnk。",
                        }
                    },
                    "required": ["item_name"],
                    "additionalProperties": False,
                },
                handler=self._open_desktop_item,
                group="desktop",
                owner="desktop_agent",
                risk="medium",
            )
        )

        registry.register(
            ToolSpec(
                name="open_file",
                description="按路径打开本地文件；支持绝对路径、~ 路径或相对当前工作目录的路径。",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要打开的文件路径，例如 C:/Users/me/notes.pdf 或 docs/report.md。",
                        }
                    },
                    "required": ["file_path"],
                    "additionalProperties": False,
                },
                handler=self._open_file,
                group="desktop",
                owner="desktop_agent",
                risk="medium",
            )
        )

    def open_url_direct(self, url: str) -> dict[str, str]:
        """供其他专长 Agent 复用的内部能力。"""
        return self.desktop_service.open_url(url)

    def _open_google(self, arguments: dict[str, Any]) -> dict[str, str]:
        if arguments:
            raise ValueError("open_google 不需要参数")
        return self.desktop_service.open_url("https://www.google.com")

    def _open_url(self, arguments: dict[str, Any]) -> dict[str, str]:
        url = arguments.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("open_url 需要非空 url")
        return self.desktop_service.open_url(url)

    def _open_desktop_item(self, arguments: dict[str, Any]) -> dict[str, str]:
        item_name = arguments.get("item_name")
        if not isinstance(item_name, str) or not item_name.strip():
            raise ValueError("open_desktop_item 需要非空 item_name")
        return self.desktop_service.open_desktop_item(item_name)

    def _open_file(self, arguments: dict[str, Any]) -> dict[str, str]:
        file_path = arguments.get("file_path")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("open_file 需要非空 file_path")
        return self.desktop_service.open_file(file_path)
