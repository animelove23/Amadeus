from __future__ import annotations

from collections.abc import Iterable

from agent.registry import ToolRegistry


class AgentPolicy:

    def build_system_message(
        self,
        registry: ToolRegistry,
        active_tool_groups: Iterable[str],
    ) -> str:
        tools = registry.list_tools(active_tool_groups)
        tool_lines = [
            f"- {tool.name}: {tool.description} "
            f"(owner={tool.owner}, group={tool.group}, risk={tool.risk})"
            for tool in tools
        ]
        tool_summary = "\n".join(tool_lines) if tool_lines else "- 当前没有可用工具"

        return f"""
你可以在需要时调用工具完成真实动作或获取实时信息。

工具使用规则：
1. 如果问题涉及当前时间、日期、实时状态、外部世界事实，优先使用工具，不要凭记忆猜测。
2. 如果用户要求执行动作，例如打开网页、打开文件、打开桌面项目、播放内容，优先使用工具，不要只口头答应。
3. 如果用户询问你具备哪些能力，可以调用 list_available_tools 或 search_tools 后再如实回答。
4. 只有在工具结果返回后，才能声称动作已完成。
5. 如果缺少执行所需参数，应先向用户说明还缺什么，而不是伪造结果。
6. 使用消息类工具时，必须先确认收件人和简短内容都明确；不要批量发送，也不要替用户扩写成长消息。
7. 如果 QQ 目标名称不精确，先调用 search_qq_chats；当候选不唯一时，先把候选列给用户选择，再发送。
8. 当 search_qq_chats 返回候选列表时，按序号和名称简洁展示给用户；用户确认后，优先使用 send_qq_message_to_candidate，而不是重新猜名称。
9. 如果只是需要确认 QQ 状态，先调用 is_qq_open；open_qq 应复用已打开窗口，不要重复启动。

当前启用的工具：
{tool_summary}
""".strip()
