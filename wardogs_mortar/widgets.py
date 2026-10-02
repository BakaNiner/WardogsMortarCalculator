from __future__ import annotations

from dataclasses import replace

import cv2
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QKeySequenceEdit, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from .config import DEFAULT_ROI, Settings
from .core import Point, Solution, bearing_text
from .win32 import exclude_from_capture


STYLE = """
QWidget { color: #e8ede7; font-family: 'Microsoft YaHei UI', 'Segoe UI'; font-size: 13px; }
QMainWindow, QDialog, QWidget#shell { background: #111813; }
QFrame#card { background: #1a231d; border: 1px solid #334237; border-radius: 12px; }
QLabel { background: transparent; }
QLabel#eyebrow { color: #b7da79; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
QLabel#title { font-size: 27px; font-weight: 700; }
QLabel#muted { color: #a6b1a8; font-size: 12px; }
QLabel#metric { color: #d5f89a; font-size: 36px; font-weight: 700; font-family: 'Consolas'; }
QLabel#pill { background: #263722; color: #c4e996; border: 1px solid #445e35; border-radius: 9px; padding: 6px 12px; }
QLabel[hotkey="true"] { background: #263722; color: #c4e996; border: 1px solid #445e35; border-radius: 7px; padding: 4px 10px; }
QLabel#error { color: #ffbb8a; }
QPushButton { background: #29372d; border: 1px solid #435448; border-radius: 7px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #354b3a; border-color: #789565; }
QPushButton:pressed { background: #1d2d21; }
QPushButton:disabled { color: #717d73; background: #202b23; border-color: #303e33; }
QPushButton#primary { background: #c3e887; color: #17220c; border-color: #c3e887; }
QPushButton#primary:hover { background: #d5f5a4; }
QPushButton#primary:disabled { background: #627349; color: #253020; }
QLineEdit, QComboBox, QKeySequenceEdit { background: #101912; border: 1px solid #435448; border-radius: 6px; padding: 9px; selection-background-color: #668548; }
QLineEdit { font-family: 'Consolas'; font-size: 19px; }
QLineEdit:focus, QKeySequenceEdit:focus { border-color: #c3e887; }
QComboBox QAbstractItemView { background: #18241b; selection-background-color: #3b523c; }
QToolTip { background: #26372a; color: #eef5e9; border: 1px solid #65845c; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { background: #344a37; height: 5px; border-radius: 2px; }
QSlider::handle:horizontal { background: #c3e887; width: 15px; margin: -5px 0; border-radius: 7px; }
QStatusBar { color: #acb8ae; background: #111813; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #111813; width: 10px; }
QScrollBar::handle:vertical { background: #435448; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""


def label(text: str, name: str = "") -> QLabel:
    item = QLabel(text)
    if name:
        item.setObjectName(name)
    return item


def pixmap(image) -> QPixmap:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return QPixmap.fromImage(QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format.Format_RGB888).copy())


class Overlay(QWidget):
    moved = Signal()

    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setWindowTitle("WARDOGS · 射击参数")
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(STYLE + "QWidget#overlay { background: #152019; border: 1px solid #62764d; border-radius: 10px; }")
        self.setObjectName("overlay")
        self.setFixedSize(414, 168)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        self.heading = label("L81  /  等待坐标", "eyebrow")
        layout.addWidget(self.heading)
        row = QHBoxLayout()
        self.values = []
        for caption in ("方位角", "距离 · m", "仰角 · MIL"):
            col = QVBoxLayout()
            col.addWidget(label(caption, "muted"))
            value = label("—", "metric")
            value.setStyleSheet("font-size: 29px")
            col.addWidget(value)
            self.values.append(value)
            row.addLayout(col)
        layout.addLayout(row)
        self.status = label("打开地图，记录炮位和目标", "muted")
        layout.addWidget(self.status)
        self.drag_offset = None

    def showEvent(self, event):
        super().showEvent(event)
        exclude_from_capture(int(self.winId()))

    def update_solution(self, solution: Solution | None):
        if solution:
            self.values[0].setText(bearing_text(solution.bearing))
            self.values[1].setText(f"{solution.distance:.0f}")
            self.values[2].setText(f"{solution.mil:.0f}" if solution.mil is not None else "—")
            self.status.setText(solution.status + " · 平地射表")
        else:
            for value in self.values:
                value.setText("—")
            self.status.setText("等待炮位和目标坐标")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        self.moved.emit()


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, displays: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键与显示设置")
        self.setMinimumWidth(480)
        self.original = settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(label("快捷键与显示", "title"))
        form = QFormLayout()
        form.setSpacing(14)
        self.keys = {}
        for attr, caption in (("origin_hotkey", "记录炮位"), ("target_hotkey", "记录目标"), ("overlay_hotkey", "显示 / 隐藏悬浮窗")):
            edit = QKeySequenceEdit(QKeySequence(getattr(settings, attr)))
            edit.setMaximumSequenceLength(1)
            edit.setAccessibleName(caption + "快捷键")
            form.addRow(caption, edit)
            self.keys[attr] = edit
        self.monitor = QComboBox()
        for i, display in enumerate(displays, 1):
            self.monitor.addItem(f"显示器 {i} · {display['width']} × {display['height']}", i)
        self.monitor.setCurrentIndex(max(0, min(settings.monitor-1, len(displays)-1)))
        form.addRow("游戏显示器", self.monitor)
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(35, 100)
        self.opacity.setValue(settings.overlay_opacity)
        form.addRow("悬浮窗不透明度", self.opacity)
        self.sound = QCheckBox("识别成功时播放提示音")
        self.sound.setChecked(settings.sound)
        form.addRow(self.sound)
        layout.addLayout(form)
        hint = label("支持功能键或 Ctrl / Alt / Shift 组合键。F12 为系统保留键。\n选择游戏中未占用的按键；更换显示器后请重新框选地图。", "muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.error = label("", "error")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox()
        buttons.addButton("保存", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> Settings:
        return replace(self.original, **{key: edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) for key, edit in self.keys.items()}, monitor=self.monitor.currentData(), overlay_opacity=self.opacity.value(), sound=self.sound.isChecked())


class RegionCanvas(QWidget):
    def __init__(self, image, roi):
        super().__init__()
        self.image = pixmap(image)
        self.roi = list(roi)
        self.anchor = None
        self.setMinimumSize(600, 360)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def image_rect(self):
        size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        return QRectF((self.width()-size.width())/2, (self.height()-size.height())/2, size.width(), size.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.image_rect()
        painter.drawPixmap(rect.toRect(), self.image)
        painter.fillRect(rect, QColor(0, 0, 0, 90))
        x, y, w, h = self.roi
        selected = QRectF(rect.x()+x*rect.width(), rect.y()+y*rect.height(), w*rect.width(), h*rect.height())
        painter.setPen(QPen(QColor("#d0f596"), 2))
        painter.drawRect(selected)
        painter.fillRect(selected, QColor(185, 229, 131, 35))

    def normalized(self, pos):
        rect = self.image_rect()
        return (min(1., max(0., (pos.x()-rect.x())/rect.width())), min(1., max(0., (pos.y()-rect.y())/rect.height())))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.anchor = self.normalized(event.position())

    def mouseMoveEvent(self, event):
        if self.anchor is not None:
            x, y = self.normalized(event.position())
            ax, ay = self.anchor
            self.roi = [min(ax, x), min(ay, y), abs(x-ax), abs(y-ay)]
            self.update()

    def mouseReleaseEvent(self, event):
        self.mouseMoveEvent(event)
        self.anchor = None


class RegionDialog(QDialog):
    def __init__(self, image, roi, parent=None):
        super().__init__(parent)
        self.setWindowTitle("框选地图识别区域")
        self.resize(1050, 750)
        layout = QVBoxLayout(self)
        layout.addWidget(label("拖动框选整个地图，让 X / Y 坐标在移动时始终落在框内。", "muted"))
        self.canvas = RegionCanvas(image, roi)
        layout.addWidget(self.canvas, 1)
        self.error = label("", "error")
        layout.addWidget(self.error)
        buttons = QDialogButtonBox()
        reset = buttons.addButton("恢复默认区域", QDialogButtonBox.ButtonRole.ResetRole)
        reset.clicked.connect(self.reset)
        buttons.addButton("使用此区域", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def reset(self):
        self.canvas.roi = list(DEFAULT_ROI)
        self.canvas.update()

    def accept(self):
        from .config import valid_roi
        if not valid_roi(self.canvas.roi):
            self.error.setText("区域过小，请框选整个地图。")
            return
        super().accept()
