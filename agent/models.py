from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolSpec:

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    group: str = "default"
    owner: str = "core"
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

    call_id: str
    name: str
    content: str
    ok: bool


@dataclass(frozen=True)
class AgentRunResult:

    content: str
    generated_messages: list[dict[str, Any]]
    used_tools: list[str]
    steps: int
