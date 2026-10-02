"""Small, typed Win32 surface for hotkeys and passive utility windows."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import re
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal
from .i18n import error_text, tr


MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312


def parse_hotkey(text: str) -> tuple[int, int]:
    parts = text.upper().replace("CONTROL", "CTRL").replace(" ", "").split("+")
    mods = 0
    for part in parts[:-1]:
        if part not in {"CTRL", "ALT", "SHIFT"}:
            raise ValueError(tr("快捷键支持 Ctrl、Alt、Shift 组合"))
        bit = {"ALT": 1, "CTRL": 2, "SHIFT": 4}[part]
        if mods & bit:
            raise ValueError(tr("快捷键修饰键重复"))
        mods |= bit
    key = parts[-1]
    if key == "F12":
        raise ValueError(tr("F12 是 Windows 保留键，请选择其他快捷键"))
    if re.fullmatch(r"F(?:[1-9]|1[0-9]|2[0-4])", key):
        vk = 0x70 + int(key[1:]) - 1
    elif re.fullmatch(r"[A-Z0-9]", key) and mods:
        vk = ord(key)
    else:
        raise ValueError(tr("请使用 F1–F11、F13–F24，或 Ctrl/Alt/Shift + 字母/数字"))
    return mods | MOD_NOREPEAT, vk


if sys.platform == "win32":
    USER32 = ctypes.WinDLL("user32", use_last_error=True)
    USER32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    USER32.RegisterHotKey.restype = wintypes.BOOL
    USER32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    USER32.UnregisterHotKey.restype = wintypes.BOOL
    USER32.GetForegroundWindow.restype = wintypes.HWND
    USER32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    USER32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    USER32.SetWindowDisplayAffinity.restype = wintypes.BOOL


def own_window_in_foreground() -> bool:
    if sys.platform != "win32":
        return False
    pid = wintypes.DWORD()
    USER32.GetWindowThreadProcessId(USER32.GetForegroundWindow(), ctypes.byref(pid))
    return pid.value == os.getpid()


def exclude_from_capture(hwnd: int) -> bool:
    return bool(USER32.SetWindowDisplayAffinity(hwnd, 0x11)) if sys.platform == "win32" else False


class _HotkeySignals(QObject):
    triggered = Signal(str)


class HotkeyManager(QAbstractNativeEventFilter):
    """Qt owns the message loop; register against the main window's HWND."""
    def __init__(self, hwnd: int):
        super().__init__()
        self.hwnd = hwnd
        self.signals = _HotkeySignals()
        self.bindings: dict[str, str] = {}
        self.ids: dict[int, str] = {}

    def _register(self, bindings):
        for index, (role, key) in enumerate(bindings.items(), start=0x5100):
            mods, vk = parse_hotkey(key)
            if sys.platform != "win32" or not USER32.RegisterHotKey(self.hwnd, index, mods, vk):
                self.unregister()
                raise ValueError(tr("快捷键 {key} 注册失败，可能已被其他软件占用", key=key))
            self.ids[index] = role
        self.bindings = dict(bindings)

    def replace(self, bindings: dict[str, str]):
        parsed = [parse_hotkey(value) for value in bindings.values()]
        if len(set(parsed)) != len(parsed):
            raise ValueError(tr("炮位、目标、悬浮窗必须使用不同快捷键"))
        old = self.bindings.copy()
        self.unregister()
        try:
            self._register(bindings)
        except ValueError as exc:
            try:
                self._register(old)
            except ValueError:
                raise ValueError(tr("{error}；旧快捷键也无法恢复，请重新设置", error=error_text(exc))) from exc
            raise

    def unregister(self):
        if sys.platform == "win32":
            for index in self.ids:
                USER32.UnregisterHotKey(self.hwnd, index)
        self.ids.clear()
        self.bindings.clear()

    def nativeEventFilter(self, event_type, message):
        if sys.platform == "win32" and bytes(event_type) in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in self.ids:
                self.signals.triggered.emit(self.ids[msg.wParam])
                return True, 0
        return False, 0
