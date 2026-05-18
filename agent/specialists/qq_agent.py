from __future__ import annotations

from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry
from services.qq_service import QQService


class QQAgent:
    """负责 QQ 打开与短消息发送的专长 Agent。"""

    def __init__(self, qq_service: QQService | None = None) -> None:
        self.qq_service = qq_service or QQService()

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            ToolSpec(
                name="open_qq",
                description="打开 QQ 桌面客户端。",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                handler=self._open_qq,
                group="messaging",
                owner="qq_agent",
                risk="medium",
            )
        )

        registry.register(
            ToolSpec(
                name="send_qq_message",
                description="向指定 QQ 联系人或群聊发送一条简短消息；一次只发送一条。",
                parameters={
                    "type": "object",
                    "properties": {
                        "chat_type": {
                            "type": "string",
                            "enum": ["contact", "group"],
                            "description": "消息目标类型。",
                        },
                        "recipient_name": {
                            "type": "string",
                            "description": "联系人或群聊的准确名称。",
                        },
                        "message": {
                            "type": "string",
                            "description": "要发送的简短消息，最多 60 个字符。",
                        },
                    },
                    "required": ["chat_type", "recipient_name", "message"],
                    "additionalProperties": False,
                },
                handler=self._send_qq_message,
                group="messaging",
                owner="qq_agent",
                risk="high",
            )
        )

    def _open_qq(self, arguments: dict[str, Any]) -> dict[str, str]:
        if arguments:
            raise ValueError("open_qq 不需要参数")
        return self.qq_service.open_qq()

    def _send_qq_message(self, arguments: dict[str, Any]) -> dict[str, str]:
        chat_type = arguments.get("chat_type")
        recipient_name = arguments.get("recipient_name")
        message = arguments.get("message")

        if not isinstance(chat_type, str) or not chat_type.strip():
            raise ValueError("send_qq_message 需要非空 chat_type")
        if not isinstance(recipient_name, str) or not recipient_name.strip():
            raise ValueError("send_qq_message 需要非空 recipient_name")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("send_qq_message 需要非空 message")

        return self.qq_service.send_short_message(
            chat_type=chat_type,
            recipient_name=recipient_name,
            message=message,
        )
