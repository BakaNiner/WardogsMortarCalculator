# WARDOGS 迫击炮计算器

Windows 桌面工具：按快捷键读取游戏地图上的 X/Y 坐标，计算 L81 迫击炮的方位角、水平距离和 MIL。OCR 在本机运行，模型随程序打包。

## 运行

打开 `dist/WardogsMortar/WardogsMortar.exe`。分发时请复制整个 `WardogsMortar` 文件夹，保留 `_internal` 目录。无需另装 Python。

1. 启动后等待右上角显示“OCR 就绪”。
2. 游戏使用无边框窗口模式，打开地图，把十字线指向迫击炮所在位置，按 **F1**。
3. 把十字线指向目标位置，按 **F2**。
4. 悬浮窗显示方位角、距离和 MIL；**F3** 切换悬浮窗显示。

截图中的 X/Y 是地图十字线所指位置，并不自动代表玩家或迫击炮的位置。坐标文字必须完整可见。F1/F2/F3 可在“设置”中修改，也支持 Ctrl/Alt/Shift 组合键；F12 是 Windows 保留键。

## 设置与校准

- **游戏显示器**：多显示器环境在设置中选取游戏所在屏幕。
- **框选地图区域**：点击后有 3 秒切回游戏并打开地图，随后在截图上拖动框选整个地图。默认区域针对提供的 2560×1440、16:9 截图，按屏幕比例缩放。窗口模式、不同宽高比或 UI 缩放时请重新框选。
- **3 秒后识别**：不使用快捷键时，可点击按钮并在 3 秒内切回游戏。
- **导入截图**：可导入完整游戏截图作为炮位/目标，使用当前校准区域裁剪。
- **手动输入**：输入 X/Y 后点击“应用坐标”或按 Enter；编辑过程中旧射击解会清除。
- **悬浮窗**：可拖动，支持透明度调整，更新时不主动获取键盘焦点。
- 主窗口可最小化，快捷键保持工作。托盘可重新打开窗口。关闭主窗口或托盘“退出”会完全退出并释放快捷键。

设置保存在 `%LOCALAPPDATA%/WardogsMortar/settings.json`，错误日志位于同目录的 `app.log`。炮位和目标不会跨启动保留，避免下次进入游戏时误用旧坐标。

## 识别行为

按键触发时立即截取配置区域，后台串行执行 OCR。只接受带 X/Y 标签且具有两位小数的坐标，并校验文字位置与置信度。缺失、模糊或多组候选时提示重试，保留原坐标。手动修改、清空及后续同类任务会使旧识别任务失效。

OCR 模型在启动时预加载。已打包本地模型，识别过程无需网络连接。仅在触发时截图，不持续录屏；最近一次截图只保存在内存用于预览。

## 计算与射表

```text
dx = 目标 X - 炮位 X
dy = 目标 Y - 炮位 Y
距离（米）= hypot(dx, dy) × 100
方位角（度）= degrees(atan2(dx, dy)) mod 360
```

北为 0°，东为 90°，南为 180°，西为 270°。两点重合时方位角无定义。MIL 在相邻射表数据间线性插值，仅在 132–684 米内返回；越界不外推。界面显示取整 MIL，计算过程保留原精度。

射表为社区平地数据，不含高差修正，游戏更新后可能需要重新校验。数据位于 `wardogs_mortar/data/l81.json`，含来源、获取日期与来源提交号。来源：[Apollyon / wardogs-calculator](https://github.com/apollyon-sys/wardogs-calculator/blob/main/data/weapons.json)，许可见 `licenses/Apollyon-MIT.txt`。

验收样例：炮位 `(96.80, 113.29)` → 目标 `(97.41, 107.37)` = **595.13 m / 174.12° / 323 MIL**。

## 从源码运行

Python 3.12、Windows 10/11：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe run.py
```

开发、测试与打包：

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools/check_screenshots.py
.venv\Scripts\python.exe tools/prepare_distribution.py
.venv\Scripts\python.exe -m PyInstaller WardogsMortar.spec --noconfirm
```

打包验收（需要仓库中的三张截图）：

```powershell
dist\WardogsMortar\WardogsMortar.exe --self-test screenshots artifacts\packaged
```

输出 `report.json` 及主窗口、悬浮窗、设置和区域选择界面的截图。此验收检查真实 Windows 热键注册和消息分发，不代表已验证游戏内物理按键兼容性。

测试包含方位角、射程边界、射表插值、异常 OCR、三张截图及缩放样本、快捷键解析和异步结果失效处理。真实游戏的显示模式、快捷键冲突及地图背景变化仍需在实际游戏中验证。

## 第三方软件

PySide6、RapidOCR、ONNX Runtime、OpenCV、MSS 等组件保留各自许可。打包目录中的 `licenses` 和依赖包元数据应随分发保留。项目仅使用上游的 L81 数值射表，不包含其地图或地形资源。
