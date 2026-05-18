from __future__ import annotations

import os
import webbrowser
from pathlib import Path
from urllib.parse import urlparse


class DesktopService:
    """封装真正与桌面系统交互的动作。"""

    def open_url(self, url: str) -> dict[str, str]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("只允许打开 http / https URL")

        webbrowser.open(url)
        return {"opened_url": url}

    def open_desktop_item(self, item_name: str) -> dict[str, str]:
        if not item_name.strip():
            raise ValueError("桌面项目名称不能为空")

        desktop_dir = Path.home() / "Desktop"
        target = desktop_dir / item_name
        if not target.exists():
            raise FileNotFoundError(f"桌面上找不到: {item_name}")

        os.startfile(target)  # type: ignore[attr-defined]
        return {"opened_path": str(target)}

    def open_file(self, file_path: str) -> dict[str, str]:
        if not file_path.strip():
            raise ValueError("文件路径不能为空")

        target = Path(file_path).expanduser()
        if not target.is_absolute():
            target = Path.cwd() / target
        target = target.resolve()

        if not target.exists():
            raise FileNotFoundError(f"找不到文件: {target}")
        if not target.is_file():
            raise IsADirectoryError(f"目标不是文件: {target}")

        os.startfile(target)  # type: ignore[attr-defined]
        return {"opened_path": str(target)}
