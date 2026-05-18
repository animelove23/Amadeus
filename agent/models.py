from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolSpec:
    """一个可被模型调用的工具定义。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    group: str = "default"
    risk: str = "low"

    def to_model_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class ToolCall:
    """模型返回的一次工具调用请求。"""

    call_id: str
    name: str
    arguments: str | dict[str, Any]
    call_type: str = "function"

    def to_message_payload(self) -> dict[str, Any]:
        return {
            "id": self.call_id,
            "type": self.call_type,
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass(frozen=True)
class ToolResult:
    """工具执行后的统一结果。"""

    call_id: str
    name: str
    content: str
    ok: bool


@dataclass(frozen=True)
class AgentRunResult:
    """一次 Agent 回合的最终结果。"""

    content: str
    generated_messages: list[dict[str, Any]]
    used_tools: list[str]
    steps: int
