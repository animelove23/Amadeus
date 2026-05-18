from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from agent.models import ToolSpec


class ToolRegistry:

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._groups: dict[str, set[str]] = defaultdict(set)

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"工具已存在: {tool.name}")

        self._tools[tool.name] = tool
        self._groups[tool.group].add(tool.name)

    def get(self, tool_name: str) -> ToolSpec | None:
        return self._tools.get(tool_name)

    def schemas(self, groups: Iterable[str] | None = None) -> list[dict[str, Any]]:
        allowed_names = self._resolve_tool_names(groups)
        return [self._tools[name].to_model_schema() for name in allowed_names]

    def list_groups(self) -> list[str]:
        return sorted(self._groups)

    def list_tools(self, groups: Iterable[str] | None = None) -> list[ToolSpec]:
        allowed_names = self._resolve_tool_names(groups)
        return [self._tools[name] for name in allowed_names]

    def search(self, query: str) -> list[ToolSpec]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return list(self._tools.values())

        return [
            tool
            for tool in self._tools.values()
            if normalized_query in tool.name.lower()
            or normalized_query in tool.description.lower()
            or normalized_query in tool.group.lower()
            or normalized_query in tool.owner.lower()
        ]

    def _resolve_tool_names(self, groups: Iterable[str] | None) -> list[str]:
        if groups is None:
            return sorted(self._tools)

        names: set[str] = set()
        for group in groups:
            names.update(self._groups.get(group, set()))
        return sorted(names)
