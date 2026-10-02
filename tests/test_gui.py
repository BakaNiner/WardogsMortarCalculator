import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from wardogs_mortar.app import MainWindow
from wardogs_mortar.core import Point


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setenv("WARDOGS_CONFIG_DIR", str(tmp_path))
    app = QApplication.instance() or QApplication([])
    win = MainWindow(start_worker=False, register_hotkeys=False)
    yield win
    win.close()
    app.processEvents()


def test_manual_inputs_and_clear(window):
    for role, coords in (("origin", ("96.80", "113.29")), ("target", ("97.41", "107.37"))):
        for edit, value in zip(window.inputs[role], coords):
            edit.setText(value)
        window.apply_manual(role)
    assert window.metrics[0].text() == "174.1°"
    assert window.metrics[1].text() == "595.1"
    assert window.metrics[2].text() == "323"
    window.swap_points()
    assert window.metrics[0].text() == "354.1°"
    window.clear_points()
    assert window.solution is None
    assert all(metric.text() == "—" for metric in window.metrics)


def test_stale_recognition_cannot_replace_manual_edit(window):
    window.latest["origin"] = 1
    window.next_job = 1
    window.on_coordinate_edit("origin")
    result = SimpleNamespace(point=Point(12, 13))
    window.on_result(1, "origin", result)
    assert window.points["origin"] is None


def test_failure_preserves_point_and_clearing_cancels_jobs(window):
    window.set_point("origin", Point(96.8, 113.29), "test")
    window.latest["origin"] = 1
    window.next_job = 1
    window.on_failure(1, "origin", "invalid")
    assert window.points["origin"] == Point(96.8, 113.29)
    window.clear_points()
    window.on_result(1, "origin", SimpleNamespace(point=Point(12, 13)))
    assert window.points["origin"] is None

