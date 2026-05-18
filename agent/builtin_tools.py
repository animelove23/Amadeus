from datetime import datetime
from typing import Any

from agent.models import ToolSpec
from agent.registry import ToolRegistry


def register_builtin_tools(registry: ToolRegistry) -> None:
    """注册项目当前阶段保留的最小内置工具。"""
    registry.register(
        ToolSpec(
            name="get_current_time",
            description="获取运行程序这台机器的当前本地时间。",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=_get_current_time,
            group="system",
            owner="builtin",
            risk="low",
        )
    )


def _get_current_time(arguments: dict[str, Any]) -> dict[str, str]:
    if arguments:
        raise ValueError("get_current_time 不需要参数")
    return {"local_time": datetime.now().isoformat(timespec="seconds")}

