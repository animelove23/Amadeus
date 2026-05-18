from types import SimpleNamespace

from agent.executor import ToolExecutor
from agent.registry import ToolRegistry
from agent.runtime import AgentRuntime
from agent.builtin_tools import register_builtin_tools


class FakeAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def set_user_template(self, template: str) -> None:
        pass

    def chat(self, messages: list, stream: bool, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="",
                            tool_calls=[
                                SimpleNamespace(
                                    id="call_1",
                                    type="function",
                                    function=SimpleNamespace(
                                        name="get_current_time",
                                        arguments="{}",
                                    ),
                                )
                            ],
                        )
                    )
                ]
            )

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="[emotion=neutral]\n已获取当前时间。",
                        tool_calls=None,
                    )
                )
            ]
        )


def test_agent_runtime_executes_tool_and_returns_final_answer() -> None:
    registry = ToolRegistry()
    register_builtin_tools(registry)
    runtime = AgentRuntime(
        adapter=FakeAdapter(),
        registry=registry,
        executor=ToolExecutor(registry),
    )

    result = runtime.run([{"role": "user", "content": "现在几点？"}])

    assert result.content == "[emotion=neutral]\n已获取当前时间。"
    assert result.used_tools == ["get_current_time"]
    assert [message["role"] for message in result.generated_messages] == [
        "assistant",
        "tool",
        "assistant",
    ]
