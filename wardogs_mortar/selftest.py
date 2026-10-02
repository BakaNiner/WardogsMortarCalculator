"""Packaged acceptance test: real OCR worker, resources, Qt and Win32 hotkeys.

Run with --self-test SCREENSHOTS OUTPUT_DIRECTORY. Does not automate other apps.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time
import traceback

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QApplication

from .app import MainWindow
from .capture import crop_region, grab_region, monitors, read_image
from .config import DEFAULT_ROI
from .core import Point
from .widgets import RegionDialog, SettingsDialog, STYLE


def run(screenshots, destination):
    output = Path(destination).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ["WARDOGS_CONFIG_DIR"] = str(output / "test-config")
    report = {"passed": False, "frozen": bool(getattr(sys, "frozen", False)), "screenshots": []}
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.settings.sound = False
    window.show()
    dataset = [
        ("origin", "x 71.82 y 56.35.jpg", Point(71.82, 56.35)),
        ("origin", "x 96.80 y 113.29.jpg", Point(96.80, 113.29)),
        ("target", "x 97.41 y 107.37.jpg", Point(97.41, 107.37)),
    ]
    position = 0
    finished = False
    seen_hotkeys = []
    window.hotkeys.signals.triggered.connect(seen_hotkeys.append)

    def finish(error=None):
        nonlocal finished
        if finished:
            return
        finished = True
        if error:
            report["error"] = str(error)
        report["passed"] = error is None
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        window.close()
        app.exit(0 if report["passed"] else 1)

    def run_step():
        nonlocal position
        try:
            if position < len(dataset):
                role, filename, _ = dataset[position]
                frame = read_image(str(Path(screenshots) / filename))
                window.submit(role, crop_region(frame))
            else:
                verify_ui_and_hotkeys()
        except Exception:
            finish(traceback.format_exc())

    def completed(job, role, result):
        nonlocal position
        try:
            expected = dataset[position][2]
            assert result.point == expected, f"OCR mismatch: {result.point} != {expected}"
            assert window.points[role] == expected, "Worker signal did not update UI"
            report["screenshots"].append({"file": dataset[position][1], "x": result.point.x, "y": result.point.y, "seconds": round(result.elapsed, 3), "confidence": round(result.confidence, 5)})
            position += 1
            QTimer.singleShot(50, run_step)
        except Exception:
            finish(traceback.format_exc())

    def verify_ui_and_hotkeys():
        try:
            assert window.solution is not None
            assert window.metrics[0].text() == "174.1°"
            assert window.metrics[1].text() == "595.1"
            assert window.metrics[2].text() == "323"
            assert window.hotkeys.bindings, "Default hotkeys not registered"
            original = window.hotkeys.bindings.copy()
            window.hotkeys.replace({"origin": "Ctrl+Alt+F8", "target": "Ctrl+Alt+F9", "overlay": "Ctrl+Alt+F10"})
            assert len(window.hotkeys.ids) == 3
            window.hotkeys.replace(original)
            report["hotkey_registration"] = "default and custom bindings registered"
            display = monitors()[window.settings.monitor-1]
            frame = grab_region(window.settings.monitor, DEFAULT_ROI)
            assert frame.shape[0] > 10 and frame.shape[1] > 10
            report["screen_capture"] = {"width": frame.shape[1], "height": frame.shape[0], "monitor": display}
            report["solution"] = {"distance_m": window.solution.distance, "bearing_deg": window.solution.bearing, "mil": window.solution.mil}
            window.grab().save(str(output / "main.png"))
            window.overlay.grab().save(str(output / "overlay.png"))
            settings = SettingsDialog(window.settings, monitors(), window)
            settings.show()
            app.processEvents()
            settings.grab().save(str(output / "settings.png"))
            settings.close()
            region = RegionDialog(read_image(str(Path(screenshots)/dataset[-1][1])), DEFAULT_ROI, window)
            region.show()
            app.processEvents()
            region.grab().save(str(output / "region.png"))
            region.close()
            # Verify native message routing on the real application window. This
            # does not claim a physical key was received from a running game.
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
            user32.PostMessageW.restype = wintypes.BOOL
            index = next(key for key, value in window.hotkeys.ids.items() if value == "overlay")
            assert user32.PostMessageW(int(window.winId()), 0x312, index, 0)
            QTimer.singleShot(100, verify_message)
        except Exception:
            finish(traceback.format_exc())

    def verify_message():
        try:
            assert "overlay" in seen_hotkeys, "WM_HOTKEY was not delivered"
            report["native_hotkey_message"] = "received through Qt native event filter"
            finish()
        except Exception:
            finish(traceback.format_exc())

    class Receiver(QObject):
        @Slot()
        def start(self):
            run_step()

        @Slot(int, str, object)
        def result(self, job, role, result):
            completed(job, role, result)

        @Slot(int, str, str)
        def failure(self, job, role, message):
            finish(message)

        @Slot(str)
        def init_failure(self, message):
            finish(message)

    receiver = Receiver()
    window.worker.ready.connect(receiver.start)
    window.worker.completed.connect(receiver.result)
    window.worker.failed.connect(receiver.failure)
    window.worker.init_failed.connect(receiver.init_failure)
    QTimer.singleShot(45000, lambda: finish("Self-test timed out") if not finished else None)
    sys.exit(app.exec())
