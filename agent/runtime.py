from __future__ import annotations

from typing import Any, Iterable

from agent.executor import ToolExecutor
from agent.models import AgentRunResult, ToolCall
from agent.policy import AgentPolicy
from agent.registry import ToolRegistry
from llm.adapter import LLMAdapter


class AgentRuntime:
    """负责一次 Agent 回合中的模型 ↔ 工具循环。"""

    LOOP_LIMIT_TEXT = "工具调用次数过多，已停止本轮执行。"

    def __init__(
        self,
        adapter: LLMAdapter,
        registry: ToolRegistry,
        executor: ToolExecutor,
        active_tool_groups: Iterable[str] | None = None,
        max_steps: int = 4,
        policy: AgentPolicy | None = None,
    ) -> None:
        self.adapter = adapter
        self.registry = registry
        self.executor = executor
        self.active_tool_groups = tuple(active_tool_groups or registry.list_groups())
        self.max_steps = max_steps
        self.policy = policy or AgentPolicy()

    def run(self, messages: list[dict[str, Any]]) -> AgentRunResult:
        working_messages = [
            {
                "role": "system",
                "content": self.policy.build_system_message(
                    self.registry,
                    self.active_tool_groups,
                ),
            },
            *messages,
        ]
        generated_messages: list[dict[str, Any]] = []
        used_tools: list[str] = []

        for step in range(1, self.max_steps + 1):
            response = self.adapter.chat(
                messages=working_messages,
                stream=False,
                tools=self.registry.schemas(self.active_tool_groups),
            )

            if response is None:
                return AgentRunResult(
                    content="模型调用失败，请稍后再试。",
                    generated_messages=generated_messages,
                    used_tools=used_tools,
                    steps=step,
                )

            assistant_message = response.choices[0].message
            assistant_content = self._read_attr(assistant_message, "content") or ""
            tool_calls = self._normalize_tool_calls(
                self._read_attr(assistant_message, "tool_calls")
            )

            if not tool_calls:
                final_message = {"role": "assistant", "content": assistant_content}
                generated_messages.append(final_message)
                return AgentRunResult(
                    content=assistant_content,
                    generated_messages=generated_messages,
                    used_tools=used_tools,
                    steps=step,
                )

            assistant_tool_message = {
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": [tool_call.to_message_payload() for tool_call in tool_calls],
            }
            generated_messages.append(assistant_tool_message)
            working_messages.append(assistant_tool_message)

            for tool_call in tool_calls:
                tool_result = self.executor.execute(tool_call)
                used_tools.append(tool_call.name)
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_result.call_id,
                    "name": tool_result.name,
                    "content": tool_result.content,
                }
                generated_messages.append(tool_message)
                working_messages.append(tool_message)

        final_message = {"role": "assistant", "content": self.LOOP_LIMIT_TEXT}
        generated_messages.append(final_message)
        return AgentRunResult(
            content=self.LOOP_LIMIT_TEXT,
            generated_messages=generated_messages,
            used_tools=used_tools,
            steps=self.max_steps,
        )

    def _normalize_tool_calls(self, raw_tool_calls: Any) -> list[ToolCall]:
        normalized_calls: list[ToolCall] = []

        for raw_tool_call in raw_tool_calls or []:
            raw_function = self._read_attr(raw_tool_call, "function", {})
            normalized_calls.append(
                ToolCall(
                    call_id=self._read_attr(raw_tool_call, "id", ""),
                    call_type=self._read_attr(raw_tool_call, "type", "function"),
                    name=self._read_attr(raw_function, "name", ""),
                    arguments=self._read_attr(raw_function, "arguments", "{}"),
                )
            )

        return normalized_calls

    def _read_attr(self, value: Any, name: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)
