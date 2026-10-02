from __future__ import annotations

import logging
import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import QObject, QPoint, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QDoubleValidator, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)

from .capture import crop_region, grab_monitor, grab_region, monitors, read_image
from .config import DEFAULT_ROI, Settings, data_dir
from .core import Point, bearing_text, calculate
from .widgets import Overlay, RegionDialog, SettingsDialog, STYLE, label, pixmap
from .win32 import HotkeyManager, own_window_in_foreground

LOG = logging.getLogger(__name__)
ROLE_NAMES = {"origin": "炮位", "target": "目标"}


def app_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(QColor("#19241b"))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#c3e887"), 4))
    painter.drawEllipse(14, 14, 36, 36)
    for a, b, c, d in ((32, 4, 32, 22), (32, 42, 32, 60), (4, 32, 22, 32), (42, 32, 60, 32)):
        painter.drawLine(a, b, c, d)
    painter.setBrush(QColor("#c3e887"))
    painter.drawEllipse(28, 28, 8, 8)
    painter.end()
    return QIcon(pm)


class OcrWorker(QObject):
    ready = Signal()
    init_failed = Signal(str)
    completed = Signal(int, str, object)
    failed = Signal(int, str, str)

    @Slot()
    def initialize(self):
        try:
            from .ocr import CoordinateReader
            self.reader = CoordinateReader()
            self.ready.emit()
        except Exception as exc:
            LOG.exception("OCR initialization failed")
            self.init_failed.emit(str(exc))

    @Slot(int, str, object)
    def recognize(self, job: int, role: str, image):
        try:
            result = self.reader.read(image)
            self.completed.emit(job, role, result)
        except Exception as exc:
            LOG.exception("OCR recognition failed")
            self.failed.emit(job, role, str(exc))


class MainWindow(QMainWindow):
    recognize = Signal(int, str, object)

    def __init__(self, start_worker=True, register_hotkeys=True):
        super().__init__()
        self.setWindowTitle("WARDOGS 迫击炮计算器")
        self.setWindowIcon(app_icon())
        self.resize(1040, 840)
        self.setMinimumSize(880, 680)
        self.settings = Settings.load()
        self.points: dict[str, Point | None] = {"origin": None, "target": None}
        self.latest = {"origin": 0, "target": 0}
        self.next_job = 0
        self.pending = set()
        self.ready = False
        self.closing = False
        self.calibrating = False
        self.preview_pixmap = None
        self.solution = None
        self.hotkeys = None
        self.thread = None
        self._build_ui()
        self.overlay = Overlay()
        self.overlay.setWindowIcon(self.windowIcon())
        self.overlay.moved.connect(self.save_overlay_position)
        self._place_overlay()
        self.apply_display_settings()
        self._build_tray()
        if register_hotkeys:
            self.hotkeys = HotkeyManager(int(self.winId()))
            QApplication.instance().installNativeEventFilter(self.hotkeys)
            self.hotkeys.signals.triggered.connect(self.on_hotkey)
            self.register_keys()
        if start_worker:
            self.thread = QThread(self)
            self.worker = OcrWorker()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.initialize)
            self.recognize.connect(self.worker.recognize)
            self.worker.ready.connect(self.ocr_ready)
            self.worker.init_failed.connect(self.ocr_unavailable)
            self.worker.completed.connect(self.on_result)
            self.worker.failed.connect(self.on_failure)
            self.thread.finished.connect(self.worker.deleteLater)
            self.thread.start()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        shell = QWidget()
        shell.setObjectName("shell")
        root = QVBoxLayout(shell)
        root.setContentsMargins(26, 22, 26, 18)
        root.setSpacing(18)
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(4)
        titles.addWidget(label("WARDOGS  /  FIRE CONTROL", "eyebrow"))
        titles.addWidget(label("迫击炮计算器", "title"))
        titles.addWidget(label("选中地图坐标，按下快捷键。射击参数自动更新。", "muted"))
        top.addLayout(titles, 1)
        self.engine_status = label("正在加载 OCR…", "pill")
        top.addWidget(self.engine_status, 0, Qt.AlignmentFlag.AlignVCenter)
        settings = QPushButton("设置")
        settings.clicked.connect(self.open_settings)
        top.addWidget(settings)
        root.addLayout(top)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.inputs = {}
        self.capture_buttons = {}
        self.file_buttons = {}
        self.point_status = {}
        for role, caption in ROLE_NAMES.items():
            frame = QFrame()
            frame.setObjectName("card")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(20, 17, 20, 17)
            layout.setSpacing(12)
            heading = QHBoxLayout()
            heading.addWidget(label("01  /  迫击炮位置" if role == "origin" else "02  /  目标位置", "eyebrow"))
            heading.addStretch()
            key = getattr(self.settings, f"{role}_hotkey")
            key_label = label(key, "pill")
            key_label.setObjectName(f"{role}Key")
            key_label.setProperty("hotkey", True)
            heading.addWidget(key_label)
            layout.addLayout(heading)
            row = QHBoxLayout()
            fields = []
            for axis in ("X", "Y"):
                col = QVBoxLayout()
                col.setSpacing(4)
                col.addWidget(label(axis + (" · 东向" if axis == "X" else " · 北向"), "muted"))
                edit = QLineEdit()
                edit.setPlaceholderText("0.00")
                edit.setAccessibleName(caption + axis + "坐标")
                validator = QDoubleValidator(0, 999.99, 2, edit)
                validator.setNotation(QDoubleValidator.Notation.StandardNotation)
                from PySide6.QtCore import QLocale
                validator.setLocale(QLocale.c())
                edit.setValidator(validator)
                edit.returnPressed.connect(lambda role=role: self.apply_manual(role))
                edit.textEdited.connect(lambda _text, role=role: self.on_coordinate_edit(role))
                fields.append(edit)
                col.addWidget(edit)
                row.addLayout(col)
            self.inputs[role] = fields
            layout.addLayout(row)
            buttons = QHBoxLayout()
            capture = QPushButton("3 秒后识别" + caption)
            capture.setObjectName("primary")
            capture.setEnabled(False)
            capture.clicked.connect(lambda checked=False, role=role: self.delayed_capture(role))
            capture.setToolTip("点击后切回游戏并指向地图位置，3 秒后截取画面")
            self.capture_buttons[role] = capture
            buttons.addWidget(capture, 1)
            apply = QPushButton("应用坐标")
            apply.clicked.connect(lambda checked=False, role=role: self.apply_manual(role))
            buttons.addWidget(apply)
            layout.addLayout(buttons)
            footer = QHBoxLayout()
            source = label("尚未记录", "muted")
            self.point_status[role] = source
            footer.addWidget(source, 1)
            import_button = QPushButton("导入截图")
            import_button.setAccessibleName("导入" + caption + "截图")
            import_button.setEnabled(False)
            import_button.clicked.connect(lambda checked=False, role=role: self.import_image(role))
            footer.addWidget(import_button)
            self.file_buttons[role] = import_button
            layout.addLayout(footer)
            cards.addWidget(frame, 1)
        root.addLayout(cards)

        solution_frame = QFrame()
        solution_frame.setObjectName("card")
        sol = QVBoxLayout(solution_frame)
        sol.setContentsMargins(22, 16, 22, 18)
        bar = QHBoxLayout()
        bar.addWidget(label("FIRING SOLUTION", "eyebrow"), 1)
        bar.addWidget(label("L81 迫击炮  ·  132–684 m", "muted"))
        sol.addLayout(bar)
        metrics = QHBoxLayout()
        self.metrics = []
        for title in ("方位角 / AZIMUTH", "水平距离 / METERS", "仰角设置 / MIL"):
            col = QVBoxLayout()
            col.addWidget(label(title, "muted"))
            value = label("—", "metric")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.metrics.append(value)
            col.addWidget(value)
            metrics.addLayout(col, 1)
        sol.addLayout(metrics)
        bottom = QHBoxLayout()
        self.range_status = label("等待炮位和目标坐标", "muted")
        bottom.addWidget(self.range_status, 1)
        self.copy_button = QPushButton("复制结果")
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.setEnabled(False)
        bottom.addWidget(self.copy_button)
        swap = QPushButton("交换位置")
        swap.clicked.connect(self.swap_points)
        bottom.addWidget(swap)
        clear = QPushButton("清空")
        clear.clicked.connect(self.clear_points)
        bottom.addWidget(clear)
        sol.addLayout(bottom)
        root.addWidget(solution_frame)

        lower = QHBoxLayout()
        lower.setSpacing(16)
        activity_frame = QFrame()
        activity_frame.setObjectName("card")
        activity = QVBoxLayout(activity_frame)
        activity.setContentsMargins(20, 16, 20, 16)
        activity.addWidget(label("识别状态", "eyebrow"))
        self.activity = label("正在预加载本地识别模型…")
        self.activity.setWordWrap(True)
        self.activity.setMinimumHeight(48)
        activity.addWidget(self.activity)
        self.help = label("1. 地图十字线指向炮位 → F1\n2. 指向目标 → F2\n3. 按 F3 显示 / 隐藏悬浮窗", "muted")
        self.help.setWordWrap(True)
        activity.addWidget(self.help)
        actions = QHBoxLayout()
        self.calibrate_button = QPushButton("框选地图区域")
        self.calibrate_button.clicked.connect(self.start_calibration)
        actions.addWidget(self.calibrate_button)
        self.overlay_button = QPushButton("隐藏悬浮窗")
        self.overlay_button.clicked.connect(self.toggle_overlay)
        actions.addWidget(self.overlay_button)
        activity.addLayout(actions)
        lower.addWidget(activity_frame, 3)

        preview_frame = QFrame()
        preview_frame.setObjectName("card")
        preview_box = QVBoxLayout(preview_frame)
        preview_box.setContentsMargins(16, 14, 16, 14)
        preview_box.addWidget(label("最近一次识别画面", "eyebrow"))
        self.preview = label("识别后显示地图截取区域", "muted")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(230, 120)
        self.preview.setMaximumHeight(150)
        preview_box.addWidget(self.preview, 1)
        lower.addWidget(preview_frame, 2)
        root.addLayout(lower)
        foot = label("1 坐标单位 = 100 m  ·  0° 北 / 90° 东  ·  MIL 使用社区平地射表，未修正地形高差", "muted")
        foot.setWordWrap(True)
        root.addWidget(foot)
        root.addStretch()
        scroll.setWidget(shell)
        self.setCentralWidget(scroll)
        self.statusBar().showMessage("本地识别 · 配置保存在 " + str(data_dir()))

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("WARDOGS 迫击炮计算器")
        menu = QMenu()
        show = menu.addAction("打开主窗口")
        show.triggered.connect(self.show_main)
        toggle = menu.addAction("显示 / 隐藏悬浮窗")
        toggle.triggered.connect(self.toggle_overlay)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show_main() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()

    def _place_overlay(self):
        pos = self.settings.overlay_position
        if pos and any(screen.availableGeometry().contains(QPoint(*pos)) for screen in QApplication.screens()):
            self.overlay.move(*pos)
        else:
            area = QApplication.primaryScreen().availableGeometry()
            self.overlay.move(area.right()-self.overlay.width()-24, area.top()+24)

    def show_main(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def save_settings(self):
        try:
            self.settings.save()
        except OSError as exc:
            self.statusBar().showMessage("设置保存失败：" + str(exc))

    def save_overlay_position(self):
        self.settings.overlay_position = [self.overlay.x(), self.overlay.y()]
        self.save_settings()

    def apply_display_settings(self):
        self.overlay.setWindowOpacity(self.settings.overlay_opacity / 100)
        self.overlay.setVisible(self.settings.overlay_visible)
        self.overlay.heading.setText(f"L81  /  {self.settings.origin_hotkey} 炮位  ·  {self.settings.target_hotkey} 目标")
        self.overlay_button.setText("隐藏悬浮窗" if self.settings.overlay_visible else "显示悬浮窗")
        for role in ROLE_NAMES:
            self.findChild(QLabel, f"{role}Key").setText(getattr(self.settings, f"{role}_hotkey"))
        self.help.setText(f"1. 地图十字线指向炮位 → {self.settings.origin_hotkey}\n2. 指向目标 → {self.settings.target_hotkey}\n3. 按 {self.settings.overlay_hotkey} 显示 / 隐藏悬浮窗")

    def register_keys(self):
        try:
            self.hotkeys.replace(self.key_bindings(self.settings))
        except ValueError as exc:
            self.activity.setText(str(exc) + "。可在设置中更换快捷键，或使用导入截图。")
            self.statusBar().showMessage(str(exc))

    @staticmethod
    def key_bindings(settings):
        return {"origin": settings.origin_hotkey, "target": settings.target_hotkey, "overlay": settings.overlay_hotkey}

    def open_settings(self):
        try:
            dialog = SettingsDialog(self.settings, monitors(), self)
        except Exception as exc:
            self.activity.setText(str(exc))
            return
        previous_bindings = self.hotkeys.bindings.copy() if self.hotkeys else {}
        if self.hotkeys:
            # Let QKeySequenceEdit receive keys that were previously global.
            self.hotkeys.unregister()
        # Validate and commit hotkeys before closing the dialog.
        def accept():
            try:
                proposed = dialog.values()
                if self.hotkeys:
                    self.hotkeys.replace(self.key_bindings(proposed))
                if proposed.monitor != self.settings.monitor:
                    proposed.roi = list(DEFAULT_ROI)
                self.settings = proposed
                self.save_settings()
                self.apply_display_settings()
                from PySide6.QtWidgets import QDialog
                QDialog.accept(dialog)
            except ValueError as exc:
                dialog.error.setText(str(exc))
        # Buttons are connected to the bound accept method at construction;
        # replace their accepted connection explicitly.
        from PySide6.QtWidgets import QDialogButtonBox
        box = dialog.findChild(QDialogButtonBox)
        box.accepted.disconnect()
        box.accepted.connect(accept)
        if not dialog.exec() and self.hotkeys:
            try:
                self.hotkeys.replace(previous_bindings)
            except ValueError as exc:
                self.activity.setText(str(exc))

    def toggle_overlay(self):
        self.settings.overlay_visible = not self.settings.overlay_visible
        self.apply_display_settings()
        self.save_settings()

    @Slot()
    def ocr_ready(self):
        self.ready = True
        self.engine_status.setText("● 本地 OCR 就绪")
        for button in (*self.capture_buttons.values(), *self.file_buttons.values()):
            button.setEnabled(True)
        if self.hotkeys and not self.hotkeys.bindings:
            self.activity.setText("OCR 已就绪，但快捷键未启用。请在设置中选择未被占用的快捷键。")
        else:
            self.activity.setText("已就绪。打开游戏地图，指向位置后按快捷键记录。")

    @Slot(str)
    def ocr_unavailable(self, message):
        self.engine_status.setText("OCR 加载失败")
        self.activity.setText("识别模型加载失败，仍可手动输入坐标。" + message)

    def on_hotkey(self, role):
        if role == "overlay":
            self.toggle_overlay()
        elif QApplication.activeModalWidget() is None and not self.calibrating:
            if own_window_in_foreground():
                self.activity.setText("请切回游戏后按快捷键，或使用“3 秒后识别”按钮。")
            else:
                self.capture(role)

    def delayed_capture(self, role):
        if self.calibrating:
            return
        self.activity.setText(f"3 秒后记录{ROLE_NAMES[role]}，请切回游戏并指向地图位置…")
        self.showMinimized()
        QTimer.singleShot(3000, lambda: self.capture(role) if not self.closing else None)

    def capture(self, role):
        if not self.ready or self.calibrating:
            self.activity.setText("识别模型尚未就绪，或正在框选区域")
            return
        try:
            # Snapshot now, not when the queued OCR worker eventually runs.
            self.submit(role, grab_region(self.settings.monitor, self.settings.roi))
        except Exception as exc:
            self.report_error(str(exc))

    def import_image(self, role):
        path, _ = QFileDialog.getOpenFileName(self, "导入完整游戏截图作为" + ROLE_NAMES[role], "", "游戏截图 (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        try:
            self.submit(role, crop_region(read_image(path), self.settings.roi))
        except Exception as exc:
            self.report_error(str(exc))

    def submit(self, role, image):
        if not self.ready:
            self.report_error("OCR 模型还未就绪")
            return
        if len(self.pending) >= 4:
            self.report_error("正在处理截图，请稍后重试")
            return
        self.next_job += 1
        job = self.next_job
        self.latest[role] = job
        self.pending.add(job)
        self.show_preview(image)
        self.activity.setText(f"正在识别{ROLE_NAMES[role]}坐标…")
        self.overlay.status.setText(f"正在识别{ROLE_NAMES[role]}…")
        self.recognize.emit(job, role, image)

    def show_preview(self, image):
        self.preview_pixmap = pixmap(image)
        self.preview.setPixmap(self.preview_pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    @Slot(int, str, object)
    def on_result(self, job, role, result):
        self.pending.discard(job)
        if job != self.latest[role]:
            return
        self.set_point(role, result.point, f"识别成功 · {time.strftime('%H:%M:%S')}")
        if job == self.next_job:
            self.show_preview(result.preview)
            self.activity.setText(f"{ROLE_NAMES[role]}已记录：{result.point.label()}\n识别用时 {result.elapsed:.2f} 秒 · 置信度 {result.confidence:.1%}")
        if self.settings.sound:
            QApplication.beep()

    @Slot(int, str, str)
    def on_failure(self, job, role, message):
        self.pending.discard(job)
        if job != self.latest[role]:
            return
        self.point_status[role].setText("识别失败 · 保留原坐标")
        self.report_error(f"{ROLE_NAMES[role]}识别失败：{message}")

    def report_error(self, message):
        self.activity.setText(message)
        self.overlay.status.setText("识别失败 · 保留原值，请重试")
        self.overlay.status.setToolTip(message)

    def invalidate(self, role):
        self.next_job += 1
        self.latest[role] = self.next_job

    def on_coordinate_edit(self, role):
        self.invalidate(role)
        self.points[role] = None
        self.point_status[role].setText("坐标已编辑 · 按 Enter 或应用")
        self.update_solution()

    def apply_manual(self, role):
        try:
            fields = self.inputs[role]
            if not all(field.hasAcceptableInput() and field.text().strip() for field in fields):
                raise ValueError("请输入 0–999.99 范围内的 X/Y 坐标，最多两位小数")
            point = Point(*(float(field.text()) for field in fields))
            self.invalidate(role)
            self.set_point(role, point, "手动输入")
            self.activity.setText(f"{ROLE_NAMES[role]}已应用：{point.label()}")
        except ValueError as exc:
            self.activity.setText(str(exc))

    def set_point(self, role, point, source):
        self.points[role] = point
        for edit, value in zip(self.inputs[role], (point.x, point.y)):
            edit.setText(f"{value:.2f}")
        self.point_status[role].setText(source)
        self.update_solution()

    def update_solution(self):
        origin, target = self.points.values()
        self.solution = calculate(origin, target) if origin is not None and target is not None else None
        self.copy_button.setEnabled(self.solution is not None)
        if self.solution:
            result = self.solution
            self.metrics[0].setText(bearing_text(result.bearing))
            self.metrics[1].setText(f"{result.distance:.1f}")
            self.metrics[2].setText(f"{result.mil:.0f}" if result.mil is not None else "—")
            self.range_status.setText(result.status)
            self.range_status.setStyleSheet("color: #c3e887" if result.mil is not None else "color: #ffbb8a")
        else:
            for metric in self.metrics:
                metric.setText("—")
            self.range_status.setText("等待炮位和目标坐标")
        self.overlay.update_solution(self.solution)

    def copy_result(self):
        if self.solution:
            result = self.solution
            mil = f"{result.mil:.0f}" if result.mil is not None else "无有效解"
            QApplication.clipboard().setText(f"L81 | 炮位 {self.points['origin'].label()} | 目标 {self.points['target'].label()} | 方位 {bearing_text(result.bearing)} | 距离 {result.distance:.1f} m | MIL {mil} | {result.status}（平地射表）")
            self.activity.setText("射击参数已复制")

    def swap_points(self):
        old = self.points.copy()
        for role, other in (("origin", "target"), ("target", "origin")):
            self.invalidate(role)
            self.points[role] = old[other]
            if old[other] is None:
                for edit in self.inputs[role]:
                    edit.clear()
                self.point_status[role].setText("尚未记录")
            else:
                self.set_point(role, old[other], "交换位置")
        self.update_solution()

    def clear_points(self):
        for role in ROLE_NAMES:
            self.invalidate(role)
            self.points[role] = None
            for edit in self.inputs[role]:
                edit.clear()
            self.point_status[role].setText("尚未记录")
        self.update_solution()
        self.activity.setText("坐标已清空")

    def start_calibration(self):
        if self.calibrating:
            return
        self.calibrating = True
        self.activity.setText("3 秒后截取所选显示器，请切回游戏并打开地图…")
        self.showMinimized()
        self.overlay.hide()
        QTimer.singleShot(3000, self.finish_calibration)

    def finish_calibration(self):
        if self.closing:
            return
        try:
            image = grab_monitor(self.settings.monitor)
            self.show_main()
            dialog = RegionDialog(image, self.settings.roi, self)
            if dialog.exec():
                self.settings.roi = dialog.canvas.roi
                self.save_settings()
                self.activity.setText("地图识别区域已保存，按快捷键即可使用。")
        except Exception as exc:
            self.show_main()
            self.report_error(str(exc))
        finally:
            self.calibrating = False
            self.apply_display_settings()

    def closeEvent(self, event):
        self.closing = True
        if self.hotkeys:
            self.hotkeys.unregister()
            QApplication.instance().removeNativeEventFilter(self.hotkeys)
        self.save_overlay_position()
        self.overlay.close()
        self.tray.hide()
        if self.thread and self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.quit()
            self.thread.wait()
        event.accept()


def main():
    # On console-less builds, third-party progress/logging code still needs streams.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    logging.basicConfig(filename=data_dir() / "app.log", level=logging.INFO, encoding="utf-8", format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("WardogsMortar")
    app.setOrganizationName("WardogsMortar")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
