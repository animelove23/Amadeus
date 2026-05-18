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
    assert "is_qq_open" in tool_names
    assert "open_qq" in tool_names
    assert "search_qq_chats" in tool_names
    assert "send_qq_message" in tool_names
    assert "send_qq_message_to_candidate" in tool_names
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
        desktop_agent=desktop_agent,
        bilibili_service=FakeBilibiliService(),
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
    agent = DesktopAgent(desktop_service=service)

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
    agent = ScholarAgent(desktop_agent=desktop_agent)

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
    agent = QQAgent(qq_service=service)

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


def test_qq_service_search_returns_candidate_ids() -> None:
    from services.qq_service import QQService

    service = QQService(
        executable_candidates=[],
        search_provider=lambda keyword, chat_type, limit: [
            "机器学习交流群",
            "机器学习项目组",
            "机器学习交流群",
        ],
    )

    result = service.search_chats(keyword="机器学习", chat_type="group")

    assert result == {
        "keyword": "机器学习",
        "chat_type": "group",
        "candidates": [
            {
                "candidate_id": "group_1",
                "name": "机器学习交流群",
                "chat_type": "group",
            },
            {
                "candidate_id": "group_2",
                "name": "机器学习项目组",
                "chat_type": "group",
            },
        ],
        "requires_user_choice": True,
    }


def test_qq_agent_sends_to_confirmed_candidate() -> None:
    from agent.specialists.qq_agent import QQAgent
    from services.qq_service import QQService

    sent_messages: list[dict[str, str]] = []

    class FakeQQService(QQService):
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
                "mode": "qq_short_message",
            }
            sent_messages.append(payload)
            return payload

    service = FakeQQService(
        executable_candidates=[],
        search_provider=lambda keyword, chat_type, limit: [
            "机器学习交流群",
            "机器学习项目组",
        ],
    )
    service.search_chats(keyword="机器学习", chat_type="group")
    agent = QQAgent(qq_service=service)

    result = agent._send_qq_message_to_candidate(
        {
            "candidate_id": "group_2",
            "message": "今晚稍后回复。",
        }
    )

    assert sent_messages == [
        {
            "chat_type": "group",
            "recipient_name": "机器学习项目组",
            "message": "今晚稍后回复。",
            "mode": "qq_short_message",
        }
    ]
    assert result["recipient_name"] == "机器学习项目组"


def test_qq_service_open_qq_reuses_existing_window() -> None:
    from services.qq_service import QQService

    class FakeQQService(QQService):
        def __init__(self) -> None:
            super().__init__(executable_candidates=[])
            self.lookup_calls = 0

        def _find_qq_window(self) -> int | None:
            self.lookup_calls += 1
            return 12345

    service = FakeQQService()

    assert service.open_qq() == {
        "already_open": "true",
        "window_handle": "12345",
    }
    assert service.lookup_calls == 1


def test_qq_service_reports_closed_state() -> None:
    from services.qq_service import QQService

    class FakeQQService(QQService):
        def _find_qq_window(self) -> int | None:
            return None

    service = FakeQQService(executable_candidates=[])

    assert service.is_qq_open() == {
        "is_open": "false",
        "window_handle": "",
    }


def test_qq_service_picks_search_and_message_edits() -> None:
    from services.qq_service import QQService

    class FakeRect:
        def __init__(self, top: int) -> None:
            self.top = top

    class FakeEdit:
        def __init__(self, text: str, top: int) -> None:
            self._text = text
            self._rect = FakeRect(top)

        def window_text(self) -> str:
            return self._text

        def rectangle(self) -> FakeRect:
            return self._rect

    class FakeWindow:
        def descendants(self, **kwargs):
            assert kwargs == {"control_type": "Edit"}
            return [
                FakeEdit("搜索", 10),
                FakeEdit("", 300),
            ]

    service = QQService(executable_candidates=[])
    window = FakeWindow()

    assert service._find_search_edit(window).window_text() == "搜索"
    assert service._find_message_edit(window).rectangle().top == 300
