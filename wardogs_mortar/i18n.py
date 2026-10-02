"""Small runtime translation catalog with bindings that preserve UI state."""
from __future__ import annotations

from PySide6.QtCore import QObject


_language = "zh_CN"

EN = {
    "WARDOGS 迫击炮计算器": "WARDOGS Mortar Calculator",
    "迫击炮计算器": "Mortar Calculator",
    "炮位": "Gun",
    "目标": "Target",
    "设置": "Settings",
    "切换语言": "Switch language",
    "选中地图坐标，按下快捷键。射击参数自动更新。": "Point at a map location and press a hotkey to update your firing solution.",
    "正在加载 OCR…": "Loading OCR…",
    "01  /  迫击炮位置": "01  /  GUN POSITION",
    "02  /  目标位置": "02  /  TARGET POSITION",
    "X · 东向": "X · East",
    "Y · 北向": "Y · North",
    "{role}{axis}坐标": "{role} {axis} coordinate",
    "3 秒后识别{role}": "Capture {role} in 3s",
    "点击后切回游戏并指向地图位置，3 秒后截取画面": "Switch back to the game and point at a map location. Capture starts in 3 seconds.",
    "应用坐标": "Apply",
    "尚未记录": "Not recorded",
    "导入截图": "Import image",
    "导入{role}截图": "Import {role} screenshot",
    "L81 迫击炮  ·  132–684 m": "L81 Mortar  ·  132–684 m",
    "方位角 / AZIMUTH": "AZIMUTH / DEGREES",
    "水平距离 / METERS": "RANGE / METERS",
    "仰角设置 / MIL": "ELEVATION / MIL",
    "等待炮位和目标坐标": "Waiting for gun and target coordinates",
    "复制结果": "Copy result",
    "交换位置": "Swap",
    "清空": "Clear",
    "识别状态": "CAPTURE STATUS",
    "正在预加载本地识别模型…": "Loading the local OCR models…",
    "框选地图区域": "Select map region",
    "隐藏悬浮窗": "Hide overlay",
    "显示悬浮窗": "Show overlay",
    "最近一次识别画面": "LATEST CAPTURE",
    "识别后显示地图截取区域": "The captured map region appears here",
    "1 坐标单位 = 100 m  ·  0° 北 / 90° 东  ·  MIL 使用社区平地射表，未修正地形高差": "1 coordinate unit = 100 m  ·  0° North / 90° East  ·  Community flat-ground MIL table; no terrain correction",
    "本地识别 · 配置保存在 {path}": "Local OCR · Settings: {path}",
    "打开主窗口": "Open main window",
    "显示 / 隐藏悬浮窗": "Show / hide overlay",
    "退出": "Exit",
    "设置保存失败：{error}": "Could not save settings: {error}",
    "L81  /  {origin} 炮位  ·  {target} 目标": "L81  /  {origin} Gun  ·  {target} Target",
    "1. 地图十字线指向炮位 → {origin}\n2. 指向目标 → {target}\n3. 按 {overlay} 显示 / 隐藏悬浮窗": "1. Point at the gun on the map → {origin}\n2. Point at the target → {target}\n3. Show / hide overlay → {overlay}",
    "{error}。可在设置中更换快捷键，或使用导入截图。": "{error}. Change the hotkeys in Settings or import a screenshot.",
    "● 本地 OCR 就绪": "● Local OCR ready",
    "OCR 已就绪，但快捷键未启用。请在设置中选择未被占用的快捷键。": "OCR is ready, but hotkeys are unavailable. Choose unused hotkeys in Settings.",
    "已就绪。打开游戏地图，指向位置后按快捷键记录。": "Ready. Open the game map, point at a location, and press a capture hotkey.",
    "OCR 加载失败": "OCR unavailable",
    "识别模型加载失败，仍可手动输入坐标。{error}": "OCR could not load. You can still enter coordinates manually. {error}",
    "请切回游戏后按快捷键，或使用“3 秒后识别”按钮。": "Switch back to the game before pressing a hotkey, or use a 3-second capture button.",
    "3 秒后记录{role}，请切回游戏并指向地图位置…": "Capturing {role} in 3 seconds. Switch to the game and point at a map location…",
    "识别模型尚未就绪，或正在框选区域": "OCR is not ready, or map-region selection is in progress",
    "导入完整游戏截图作为{role}": "Import a full game screenshot for {role}",
    "游戏截图 (*.png *.jpg *.jpeg *.bmp)": "Game screenshots (*.png *.jpg *.jpeg *.bmp)",
    "OCR 模型还未就绪": "OCR is not ready yet",
    "正在处理截图，请稍后重试": "Processing captures. Please try again shortly",
    "正在识别{role}坐标…": "Reading {role} coordinates…",
    "正在识别{role}…": "Reading {role}…",
    "识别成功 · {time}": "Captured · {time}",
    "{role}已记录：{point}\n识别用时 {elapsed:.2f} 秒 · 置信度 {confidence:.1%}": "{role} recorded: {point}\nOCR took {elapsed:.2f}s · Confidence {confidence:.1%}",
    "识别失败 · 保留原坐标": "Capture failed · Previous coordinates kept",
    "{role}识别失败：{error}": "{role} capture failed: {error}",
    "识别失败 · 保留原值，请重试": "Capture failed · Previous values kept; retry",
    "坐标已编辑 · 按 Enter 或应用": "Edited · Press Enter or Apply",
    "请输入 0–999.99 范围内的 X/Y 坐标，最多两位小数": "Enter X/Y values from 0 to 999.99 with up to two decimal places",
    "手动输入": "Entered manually",
    "{role}已应用：{point}": "{role} applied: {point}",
    "无有效解": "No solution",
    "L81 | 炮位 {origin} | 目标 {target} | 方位 {bearing} | 距离 {distance:.1f} m | MIL {mil} | {status}（平地射表）": "L81 | Gun {origin} | Target {target} | Bearing {bearing} | Range {distance:.1f} m | MIL {mil} | {status} (flat-ground table)",
    "射击参数已复制": "Firing solution copied",
    "坐标已清空": "Coordinates cleared",
    "3 秒后截取所选显示器，请切回游戏并打开地图…": "Capturing the selected display in 3 seconds. Switch to the game and open the map…",
    "地图识别区域已保存，按快捷键即可使用。": "Map region saved. Press a hotkey to capture coordinates.",
    "WARDOGS · 射击参数": "WARDOGS · Firing Solution",
    "L81  /  等待坐标": "L81  /  Waiting for coordinates",
    "方位角": "Azimuth",
    "距离 · m": "Range · m",
    "仰角 · MIL": "Elevation · MIL",
    "打开地图，记录炮位和目标": "Open the map and capture gun and target",
    "{status} · 平地射表": "{status} · Flat-ground table",
    "快捷键与显示设置": "Hotkeys and Display Settings",
    "快捷键与显示": "Hotkeys & Display",
    "记录炮位": "Capture gun",
    "记录目标": "Capture target",
    "{caption}快捷键": "{caption} hotkey",
    "显示器 {index} · {width} × {height}": "Display {index} · {width} × {height}",
    "游戏显示器": "Game display",
    "悬浮窗不透明度": "Overlay opacity",
    "识别成功时播放提示音": "Play a sound after successful capture",
    "拖动滑块实时预览悬浮窗；取消后恢复原设置。\n支持功能键或 Ctrl / Alt / Shift 组合键，F12 为系统保留键。\n选择游戏中未占用的按键；更换显示器后请重新框选地图。": "Drag to preview opacity; Cancel restores your settings.\nUse function keys or Ctrl / Alt / Shift combinations; F12 is reserved.\nChoose keys unused by the game. Re-select the map region after changing displays.",
    "保存": "Save",
    "取消": "Cancel",
    "框选地图识别区域": "Select Map Capture Region",
    "拖动框选整个地图，让 X / Y 坐标在移动时始终落在框内。": "Drag to select the whole map so moving X/Y labels remain inside the region.",
    "恢复默认区域": "Reset region",
    "使用此区域": "Use this region",
    "区域过小，请框选整个地图。": "The region is too small. Select the whole map.",
    "识别区域无效，请重新框选地图": "Invalid capture region. Select the map region again",
    "显示器已断开，请在设置中重新选择": "Display disconnected. Select a display in Settings",
    "无法读取图片，请选择 PNG 或 JPG 截图": "Cannot read the image. Select a PNG or JPG screenshot",
    "坐标必须是有限数字": "Coordinates must be finite numbers",
    "射程内": "In range",
    "两点重合，方位角无定义": "Same position; bearing is undefined",
    "距离过近 · 最小 {distance} m": "Too close · Minimum {distance} m",
    "超出射程 · 最大 {distance} m": "Out of range · Maximum {distance} m",
    "未找到完整且清晰的 X/Y 坐标。请打开地图，让坐标文字完整显示后重试。": "No clear X/Y coordinate pair found. Open the map, keep both labels visible, and retry.",
    "X/Y 文字位置不匹配，请重新框选地图区域。": "X/Y labels do not match spatially. Re-select the map region.",
    "发现多组坐标，无法确定当前选点。请缩小识别区域后重试。": "Multiple coordinate pairs found. Narrow the capture region and retry.",
    "截图为空，请检查显示器与识别区域": "Empty capture. Check the display and capture region",
    "截图没有可识别内容，请尝试游戏无边框窗口模式": "No readable content in the capture. Try borderless windowed mode",
    "本地 OCR 模型缺失，请保留完整程序目录并重新解压。缺失文件：{filename}": "A local OCR model is missing. Extract the complete application folder again. Missing file: {filename}",
    "快捷键支持 Ctrl、Alt、Shift 组合": "Hotkeys support Ctrl, Alt, and Shift modifiers",
    "快捷键修饰键重复": "Duplicate hotkey modifier",
    "F12 是 Windows 保留键，请选择其他快捷键": "F12 is reserved by Windows. Choose another hotkey",
    "请使用 F1–F11、F13–F24，或 Ctrl/Alt/Shift + 字母/数字": "Use F1–F11, F13–F24, or Ctrl/Alt/Shift + a letter or digit",
    "炮位、目标、悬浮窗必须使用不同快捷键": "Gun, target, and overlay must use different hotkeys",
    "快捷键 {key} 注册失败，可能已被其他软件占用": "Cannot register {key}; another application may already use it",
    "{error}；旧快捷键也无法恢复，请重新设置": "{error}; previous hotkeys could not be restored. Configure them again",
}


def set_language(language: str):
    global _language
    _language = language if language in ("zh_CN", "en") else "zh_CN"


def language() -> str:
    return _language


class Text(str):
    """A rendered string retaining its source and format arguments for retranslation."""
    def __new__(cls, source: str, **values):
        rendered = cls.render_source(source, values)
        obj = str.__new__(cls, rendered)
        obj.source, obj.values = source, values
        return obj

    @staticmethod
    def render_source(source, values):
        template = EN.get(source, source) if _language == "en" else source
        return template.format(**{key: value.render() if isinstance(value, Text) else value for key, value in values.items()}) if values else template

    def render(self):
        return self.render_source(self.source, self.values)


def tr(source: str, **values) -> Text:
    return source if isinstance(source, Text) and not values else Text(source, **values)


def error_text(error: Exception):
    return error.args[0] if error.args and isinstance(error.args[0], Text) else str(error)


def bind(obj, method: str, source: str, **values):
    message = tr(source, **values)
    bindings = getattr(obj, "_translations", {})
    bindings[method] = message
    obj._translations = bindings
    getattr(obj, method)(message.render())


def refresh(root: QObject):
    for obj in [root, *root.findChildren(QObject)]:
        for method, message in getattr(obj, "_translations", {}).items():
            getattr(obj, method)(message.render())
