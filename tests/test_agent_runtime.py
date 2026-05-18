from types import SimpleNamespace

from agent.bootstrap import build_default_tool_registry
from agent.runtime import AgentRuntime
from agent.executor import ToolExecutor


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
    registry = build_default_tool_registry()
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


def test_default_registry_contains_specialist_agent_tools() -> None:
    registry = build_default_tool_registry()
    tool_names = {tool.name for tool in registry.list_tools()}

    assert "list_available_tools" in tool_names
    assert "search_tools" in tool_names
    assert "open_google" in tool_names
    assert "open_url" in tool_names
    assert "open_desktop_item" in tool_names
    assert "open_file" in tool_names
    assert "open_google_scholar" in tool_names
    assert "search_google_scholar" in tool_names
    assert "open_qq" in tool_names
    assert "send_qq_message" in tool_names
    assert "play_bilibili_favorite_folder" in tool_names
    assert "search_bilibili_and_open_first_video" in tool_names


def test_bilibili_search_url_is_built_for_video_results() -> None:
    from agent.specialists.bilibili_agent import BilibiliAgent
    from agent.specialists.desktop_agent import DesktopAgent

    agent = BilibiliAgent(DesktopAgent())

    assert agent.build_search_url("机器学习") == (
        "https://search.bilibili.com/video?keyword=%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0"
    )


def test_bilibili_search_tool_opens_first_video() -> None:
    from services.bilibili_service import BilibiliVideoResult
    from agent.specialists.bilibili_agent import BilibiliAgent

    class FakeDesktopAgent:
        def __init__(self) -> None:
            self.opened_urls: list[str] = []

        def open_url_direct(self, url: str) -> dict[str, str]:
            self.opened_urls.append(url)
            return {"opened_url": url}

    class FakeBilibiliService:
        def search_first_video(self, query: str) -> BilibiliVideoResult:
            assert query == "机器学习"
            return BilibiliVideoResult(
                title="机器学习入门",
                url="https://www.bilibili.com/video/BV123",
                bvid="BV123",
            )

    desktop_agent = FakeDesktopAgent()
    agent = BilibiliAgent(
        desktop_agent=desktop_agent,  # type: ignore[arg-type]
        bilibili_service=FakeBilibiliService(),  # type: ignore[arg-type]
    )

    result = agent._search_and_open_first_video({"query": "机器学习"})

    assert desktop_agent.opened_urls == ["https://www.bilibili.com/video/BV123"]
    assert result["title"] == "机器学习入门"
    assert result["mode"] == "search_first_video"


def test_desktop_agent_open_file_uses_desktop_service() -> None:
    from agent.specialists.desktop_agent import DesktopAgent

    class FakeDesktopService:
        def __init__(self) -> None:
            self.opened_files: list[str] = []

        def open_file(self, file_path: str) -> dict[str, str]:
            self.opened_files.append(file_path)
            return {"opened_path": file_path}

    service = FakeDesktopService()
    agent = DesktopAgent(desktop_service=service)  # type: ignore[arg-type]

    result = agent._open_file({"file_path": "notes.pdf"})

    assert service.opened_files == ["notes.pdf"]
    assert result == {"opened_path": "notes.pdf"}


def test_scholar_agent_builds_search_url() -> None:
    from agent.specialists.desktop_agent import DesktopAgent
    from agent.specialists.scholar_agent import ScholarAgent

    agent = ScholarAgent(DesktopAgent())

    assert agent.build_search_url("large language models") == (
        "https://scholar.google.com/scholar?q=large+language+models"
    )


def test_scholar_search_tool_opens_result_page() -> None:
    from agent.specialists.scholar_agent import ScholarAgent

    class FakeDesktopAgent:
        def __init__(self) -> None:
            self.opened_urls: list[str] = []

        def open_url_direct(self, url: str) -> dict[str, str]:
            self.opened_urls.append(url)
            return {"opened_url": url}

    desktop_agent = FakeDesktopAgent()
    agent = ScholarAgent(desktop_agent=desktop_agent)  # type: ignore[arg-type]

    result = agent._search_google_scholar({"query": "agent memory"})

    assert desktop_agent.opened_urls == ["https://scholar.google.com/scholar?q=agent+memory"]
    assert result == {
        "opened_url": "https://scholar.google.com/scholar?q=agent+memory",
        "query": "agent memory",
        "mode": "scholar_search",
    }


def test_qq_agent_sends_short_message() -> None:
    from agent.specialists.qq_agent import QQAgent

    class FakeQQService:
        def __init__(self) -> None:
            self.calls: list[dict[str, str]] = []

        def send_short_message(
            self,
            *,
            chat_type: str,
            recipient_name: str,
            message: str,
        ) -> dict[str, str]:
            payload = {
                "chat_type": chat_type,
                "recipient_name": recipient_name,
                "message": message,
            }
            self.calls.append(payload)
            return {**payload, "mode": "qq_short_message"}

    service = FakeQQService()
    agent = QQAgent(qq_service=service)  # type: ignore[arg-type]

    result = agent._send_qq_message(
        {
            "chat_type": "group",
            "recipient_name": "Agent Study Group",
            "message": "收到，稍后回复。",
        }
    )

    assert service.calls == [
        {
            "chat_type": "group",
            "recipient_name": "Agent Study Group",
            "message": "收到，稍后回复。",
        }
    ]
    assert result["mode"] == "qq_short_message"


def test_qq_service_enforces_short_messages() -> None:
    from services.qq_service import QQService

    service = QQService(executable_candidates=[])

    assert service._normalize_short_message("  收到   稍后回复  ") == "收到 稍后回复"

    try:
        service._normalize_short_message("x" * 61)
    except ValueError as error:
        assert "最多 60 个字符" in str(error)
    else:
        raise AssertionError("long messages should be rejected")
