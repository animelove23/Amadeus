from __future__ import annotations

from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry


def register_discovery_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolSpec(
            name="list_available_tools",
            description="列出当前 Agent 已注册的工具名称、归属和用途。",
            parameters={
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": "可选，按工具组过滤。",
                    }
                },
                "additionalProperties": False,
            },
            handler=lambda arguments: _list_available_tools(registry, arguments),
            group="meta",
            owner="discovery",
            risk="low",
        )
    )

    registry.register(
        ToolSpec(
            name="search_tools",
            description="按关键词搜索可用工具，适合不确定该用哪个工具时调用。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的关键词，例如 time、desktop、bilibili。",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=lambda arguments: _search_tools(registry, arguments),
            group="meta",
            owner="discovery",
            risk="low",
        )
    )


def _list_available_tools(registry: ToolRegistry, arguments: dict[str, Any]) -> dict[str, Any]:
    group = arguments.get("group")
    tools = registry.list_tools([group]) if isinstance(group, str) and group else registry.list_tools()
    return {"tools": [_tool_to_summary(tool) for tool in tools]}


def _search_tools(registry: ToolRegistry, arguments: dict[str, Any]) -> dict[str, Any]:
    query = arguments.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("search_tools 需要非空 query")
    return {"tools": [_tool_to_summary(tool) for tool in registry.search(query)]}


def _tool_to_summary(tool: ToolSpec) -> dict[str, str]:
    return {
        "name": tool.name,
        "description": tool.description,
        "group": tool.group,
        "owner": tool.owner,
        "risk": tool.risk,
    }
