from agent.builtin_tools import register_builtin_tools
from agent.discovery_tools import register_discovery_tools
from agent.registry import ToolRegistry
from agent.specialists.bilibili_agent import BilibiliAgent
from agent.specialists.desktop_agent import DesktopAgent
from agent.specialists.qq_agent import QQAgent
from agent.specialists.scholar_agent import ScholarAgent


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    desktop_agent = DesktopAgent()
    bilibili_agent = BilibiliAgent(desktop_agent=desktop_agent)
    qq_agent = QQAgent()
    scholar_agent = ScholarAgent(desktop_agent=desktop_agent)

    register_builtin_tools(registry)
    register_discovery_tools(registry)
    desktop_agent.register_tools(registry)
    bilibili_agent.register_tools(registry)
    qq_agent.register_tools(registry)
    scholar_agent.register_tools(registry)
    return registry
