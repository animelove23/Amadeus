from __future__ import annotations

import json
from typing import Any

from agent.models import ToolCall, ToolResult
from agent.registry import ToolRegistry


class ToolExecutor:
    """真正执行工具调用，并把异常也整理成模型可继续处理的结果。"""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, tool_call: ToolCall) -> ToolResult:
        tool = self.registry.get(tool_call.name)
        if tool is None:
            return self._error_result(tool_call, f"未知工具: {tool_call.name}")

        try:
            arguments = self._parse_arguments(tool_call.arguments)
            result = tool.handler(arguments)
            return ToolResult(
                call_id=tool_call.call_id,
                name=tool_call.name,
                content=self._serialize_result(result),
                ok=True,
            )
        except Exception as exc:
            return self._error_result(tool_call, f"{type(exc).__name__}: {exc}")

    def _parse_arguments(self, raw_arguments: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(raw_arguments, dict):
            return raw_arguments

        if not raw_arguments:
            return {}

        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise ValueError("工具参数必须解析成对象")
        return arguments

    def _serialize_result(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

    def _error_result(self, tool_call: ToolCall, error: str) -> ToolResult:
        return ToolResult(
            call_id=tool_call.call_id,
            name=tool_call.name,
            content=json.dumps({"error": error}, ensure_ascii=False),
            ok=False,
        )
