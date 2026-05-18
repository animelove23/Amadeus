from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from pathlib import Path
from typing import Iterable


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


class QQService:
    """封装 QQ 的基础桌面自动化动作。"""

    MAX_MESSAGE_LENGTH = 60
    DEFAULT_WINDOW_TITLE_KEYWORDS = ("QQ",)

    VK_CONTROL = 0x11
    VK_F = 0x46
    VK_V = 0x56
    VK_RETURN = 0x0D
    KEYEVENTF_KEYUP = 0x0002
    INPUT_KEYBOARD = 1
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    SW_RESTORE = 9

    def __init__(
        self,
        *,
        executable_candidates: Iterable[Path] | None = None,
        window_title_keywords: Iterable[str] | None = None,
        launch_wait_seconds: float = 4.0,
        step_wait_seconds: float = 0.5,
    ) -> None:
        self.executable_candidates = (
            tuple(executable_candidates)
            if executable_candidates is not None
            else self._build_default_executable_candidates()
        )
        self.window_title_keywords = tuple(window_title_keywords or self.DEFAULT_WINDOW_TITLE_KEYWORDS)
        self.launch_wait_seconds = launch_wait_seconds
        self.step_wait_seconds = step_wait_seconds

    def _build_default_executable_candidates(self) -> tuple[Path, ...]:
        candidates: list[Path] = []

        explicit_path = os.getenv("QQ_EXECUTABLE_PATH")
        if explicit_path:
            candidates.append(Path(explicit_path))

        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            base_dir = os.getenv(env_name)
            if base_dir:
                candidates.append(Path(base_dir) / "Tencent" / "QQNT" / "QQ.exe")

        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "Programs" / "Tencent" / "QQNT" / "QQ.exe")

        candidates.append(Path.home() / "Desktop" / "QQ.lnk")
        return tuple(candidates)

    def open_qq(self) -> dict[str, str]:
        executable = self._find_existing_executable()
        if executable is None:
            raise FileNotFoundError(
                "找不到 QQ。请设置 QQ_EXECUTABLE_PATH，或把 QQ 快捷方式放到桌面。"
            )

        os.startfile(executable)  # type: ignore[attr-defined]
        return {"opened_path": str(executable)}

    def send_short_message(
        self,
        *,
        chat_type: str,
        recipient_name: str,
        message: str,
    ) -> dict[str, str]:
        normalized_type = chat_type.strip().lower()
        if normalized_type not in {"contact", "group"}:
            raise ValueError("chat_type 只能是 contact 或 group")

        normalized_recipient = recipient_name.strip()
        if not normalized_recipient:
            raise ValueError("recipient_name 不能为空")

        normalized_message = self._normalize_short_message(message)

        self.open_qq()
        time.sleep(self.launch_wait_seconds)

        window_handle = self._find_qq_window()
        if window_handle is None:
            raise RuntimeError("已尝试打开 QQ，但没有找到可操作的 QQ 窗口")

        self._focus_window(window_handle)
        time.sleep(self.step_wait_seconds)

        self._hotkey(self.VK_CONTROL, self.VK_F)
        time.sleep(self.step_wait_seconds)
        self._paste_text(normalized_recipient)
        time.sleep(self.step_wait_seconds)
        self._press_key(self.VK_RETURN)
        time.sleep(self.step_wait_seconds)
        self._paste_text(normalized_message)
        time.sleep(self.step_wait_seconds)
        self._press_key(self.VK_RETURN)

        return {
            "chat_type": normalized_type,
            "recipient_name": normalized_recipient,
            "message": normalized_message,
            "mode": "qq_short_message",
        }

    def _find_existing_executable(self) -> Path | None:
        for candidate in self.executable_candidates:
            if candidate.exists():
                return candidate
        return None

    def _normalize_short_message(self, message: str) -> str:
        normalized = " ".join(message.split())
        if not normalized:
            raise ValueError("message 不能为空")
        if len(normalized) > self.MAX_MESSAGE_LENGTH:
            raise ValueError(f"message 过长，最多 {self.MAX_MESSAGE_LENGTH} 个字符")
        return normalized

    def _find_qq_window(self) -> int | None:
        user32 = ctypes.windll.user32
        matches: list[int] = []

        enum_callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if any(keyword.lower() in title.lower() for keyword in self.window_title_keywords):
                matches.append(hwnd)
            return True

        user32.EnumWindows(enum_callback_type(enum_callback), 0)
        return matches[0] if matches else None

    def _focus_window(self, hwnd: int) -> None:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, self.SW_RESTORE)
        if not user32.SetForegroundWindow(hwnd):
            raise RuntimeError("无法把 QQ 窗口切到前台")

    def _paste_text(self, text: str) -> None:
        self._set_clipboard_text(text)
        self._hotkey(self.VK_CONTROL, self.VK_V)

    def _set_clipboard_text(self, text: str) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        encoded = (text + "\0").encode("utf-16-le")
        if not user32.OpenClipboard(None):
            raise RuntimeError("无法打开剪贴板")

        try:
            user32.EmptyClipboard()
            handle = kernel32.GlobalAlloc(self.GMEM_MOVEABLE, len(encoded))
            if not handle:
                raise MemoryError("无法分配剪贴板内存")

            locked = kernel32.GlobalLock(handle)
            if not locked:
                raise MemoryError("无法锁定剪贴板内存")

            ctypes.memmove(locked, encoded, len(encoded))
            kernel32.GlobalUnlock(handle)

            if not user32.SetClipboardData(self.CF_UNICODETEXT, handle):
                raise RuntimeError("无法写入剪贴板")
        finally:
            user32.CloseClipboard()

    def _hotkey(self, *virtual_keys: int) -> None:
        for key in virtual_keys:
            self._send_key(key, key_up=False)
        for key in reversed(virtual_keys):
            self._send_key(key, key_up=True)

    def _press_key(self, virtual_key: int) -> None:
        self._send_key(virtual_key, key_up=False)
        self._send_key(virtual_key, key_up=True)

    def _send_key(self, virtual_key: int, *, key_up: bool) -> None:
        user32 = ctypes.windll.user32
        flags = self.KEYEVENTF_KEYUP if key_up else 0
        keyboard_input = _KEYBDINPUT(virtual_key, 0, flags, 0, None)
        input_event = _INPUT(self.INPUT_KEYBOARD, _INPUT_UNION(keyboard_input))
        sent = user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(input_event))
        if sent != 1:
            raise RuntimeError("键盘输入注入失败")
