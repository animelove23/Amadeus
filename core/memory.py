from typing import Any


ChatMessage = dict[str, Any]


class ConversationMemory:
    """只负责保存对话历史，不负责模型调用或业务编排。"""

    def __init__(self, system_prompt: str = "") -> None:
        self.system_prompt = system_prompt
        self._messages: list[ChatMessage] = []

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def extend_messages(self, messages: list[ChatMessage]) -> None:
        self._messages.extend(messages)

    def build_messages(
        self,
        extra_system_messages: list[str] | None = None,
    ) -> list[ChatMessage]:
        messages: list[ChatMessage] = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for content in extra_system_messages or []:
            if content:
                messages.append({"role": "system", "content": content})

        messages.extend(self._messages)
        return messages

    def clear(self) -> None:
        self._messages.clear()

    def get_messages(self) -> list[ChatMessage]:
        return self.build_messages()
