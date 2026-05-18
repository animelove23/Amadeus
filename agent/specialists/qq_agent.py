from __future__ import annotations

from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry
from services.qq_service import QQService


class QQAgent:

    def __init__(self, qq_service: QQService | None = None) -> None:
        self.qq_service = qq_service or QQService()

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            ToolSpec(
                name="is_qq_open",
                description="检查 QQ 桌面客户端当前是否已经打开。",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                handler=self._is_qq_open,
                group="messaging",
                owner="qq_agent",
                risk="low",
            )
        )

        registry.register(
            ToolSpec(
                name="open_qq",
                description="如果 QQ 还没打开，就打开 QQ；如果已经打开，则复用现有窗口。",
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
                name="search_qq_chats",
                description=(
                    "按关键词搜索 QQ 联系人或群聊候选，只返回候选列表，不发送消息；"
                    "当候选不唯一时，应先让用户选择。"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "聊天名称中的关键词。",
                        },
                        "chat_type": {
                            "type": "string",
                            "enum": ["contact", "group"],
                            "description": "要搜索联系人还是群聊。",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "最多返回多少个候选，默认 5。",
                        },
                    },
                    "required": ["keyword", "chat_type"],
                    "additionalProperties": False,
                },
                handler=self._search_qq_chats,
                group="messaging",
                owner="qq_agent",
                risk="medium",
            )
        )

        registry.register(
            ToolSpec(
                name="send_qq_message",
                description="向已知准确名称的 QQ 联系人或群聊发送一条简短消息；一次只发送一条。",
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

        registry.register(
            ToolSpec(
                name="send_qq_message_to_candidate",
                description="向刚刚搜索并由用户确认过的 QQ 候选对象发送一条简短消息。",
                parameters={
                    "type": "object",
                    "properties": {
                        "candidate_id": {
                            "type": "string",
                            "description": "search_qq_chats 返回的候选 id。",
                        },
                        "message": {
                            "type": "string",
                            "description": "要发送的简短消息，最多 60 个字符。",
                        },
                    },
                    "required": ["candidate_id", "message"],
                    "additionalProperties": False,
                },
                handler=self._send_qq_message_to_candidate,
                group="messaging",
                owner="qq_agent",
                risk="high",
            )
        )

    def _open_qq(self, arguments: dict[str, Any]) -> dict[str, str]:
        if arguments:
            raise ValueError("open_qq 不需要参数")
        return self.qq_service.open_qq()

    def _is_qq_open(self, arguments: dict[str, Any]) -> dict[str, str]:
        if arguments:
            raise ValueError("is_qq_open 不需要参数")
        return self.qq_service.is_qq_open()

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

    def _search_qq_chats(self, arguments: dict[str, Any]) -> dict[str, object]:
        keyword = arguments.get("keyword")
        chat_type = arguments.get("chat_type")
        limit = arguments.get("limit", 5)

        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("search_qq_chats 需要非空 keyword")
        if not isinstance(chat_type, str) or not chat_type.strip():
            raise ValueError("search_qq_chats 需要非空 chat_type")
        if not isinstance(limit, int):
            raise ValueError("search_qq_chats 的 limit 必须是整数")

        return self.qq_service.search_chats(
            keyword=keyword,
            chat_type=chat_type,
            limit=limit,
        )

    def _send_qq_message_to_candidate(self, arguments: dict[str, Any]) -> dict[str, str]:
        candidate_id = arguments.get("candidate_id")
        message = arguments.get("message")

        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("send_qq_message_to_candidate 需要非空 candidate_id")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("send_qq_message_to_candidate 需要非空 message")

        return self.qq_service.send_short_message_to_candidate(
            candidate_id=candidate_id,
            message=message,
        )
