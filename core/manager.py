from __future__ import annotations

from agent.builtin_tools import register_builtin_tools
from agent.executor import ToolExecutor
from agent.registry import ToolRegistry
from agent.runtime import AgentRuntime
from core.memory import ChatMessage, ConversationMemory
from llm.adapter import LLMAdapter
from services.rag_service import RAGService


class Manager:
    """应用编排层：组装 memory / rag / agent / adapter，而不是亲自做所有事。"""

    def __init__(
        self,
        adapter: LLMAdapter,
        system_prompt: str = "",
        memory: ConversationMemory | None = None,
        rag_service: RAGService | None = None,
        tool_registry: ToolRegistry | None = None,
        agent_runtime: AgentRuntime | None = None,
    ) -> None:
        self.adapter = adapter
        self.system_prompt = system_prompt
        self.memory = memory or ConversationMemory(system_prompt=system_prompt)
        self.rag_service = rag_service or RAGService()
        self.tool_registry = tool_registry or ToolRegistry()

        if not self.tool_registry.list_groups():
            register_builtin_tools(self.tool_registry)

        self.agent_runtime = agent_runtime or AgentRuntime(
            adapter=self.adapter,
            registry=self.tool_registry,
            executor=ToolExecutor(self.tool_registry),
        )

        self.adapter.set_user_template(system_prompt)

    def chat(self, user_input: str) -> str:
        return self._run_turn(user_input)

    def chat_stream(self, user_input: str):
        """
        当前先保持结构优先：Agent 完成整轮后，再把最终正文交给 UI。
        真正的流式 tool calling 以后应继续下沉到 AgentRuntime。
        """
        yield self._run_turn(user_input)

    def clear_messages(self) -> None:
        self.memory.clear()

    def get_messages(self) -> list[ChatMessage]:
        return self.memory.get_messages()

    def _run_turn(self, user_input: str) -> str:
        messages = self._prepare_turn(user_input)
        result = self.agent_runtime.run(messages)
        self.memory.extend_messages(result.generated_messages)
        return result.content

    def _prepare_turn(self, user_input: str) -> list[ChatMessage]:
        self.memory.add_user_message(user_input)

        retrieved_chunks = self.rag_service.retrieve(user_input)
        rag_context = self.rag_service.build_context_message(retrieved_chunks)
        extra_system_messages = [rag_context] if rag_context else []

        return self.memory.build_messages(extra_system_messages=extra_system_messages)
