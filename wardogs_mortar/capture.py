"""On-demand physical-pixel capture. No continuously running recorder."""
from __future__ import annotations

import cv2
import mss
import numpy as np

from .config import DEFAULT_ROI, valid_roi
from .i18n import tr


def monitors() -> list[dict]:
    with mss.mss() as sct:
        return [dict(left=m["left"], top=m["top"], width=m["width"], height=m["height"]) for m in sct.monitors[1:]]


def crop_region(image: np.ndarray, roi=DEFAULT_ROI) -> np.ndarray:
    if not valid_roi(roi):
        raise ValueError(tr("识别区域无效，请重新框选地图"))
    h, w = image.shape[:2]
    x, y, rw, rh = roi
    return image[round(y*h):round((y+rh)*h), round(x*w):round((x+rw)*w)].copy()


def grab_monitor(index: int) -> np.ndarray:
    with mss.mss() as sct:
        if not 1 <= index < len(sct.monitors):
            raise ValueError(tr("显示器已断开，请在设置中重新选择"))
        return np.asarray(sct.grab(sct.monitors[index]))[:, :, :3].copy()


def grab_region(index: int, roi) -> np.ndarray:
    if not valid_roi(roi):
        raise ValueError(tr("识别区域无效，请重新框选地图"))
    with mss.mss() as sct:
        if not 1 <= index < len(sct.monitors):
            raise ValueError(tr("显示器已断开，请在设置中重新选择"))
        m = sct.monitors[index]
        x, y, w, h = roi
        region = dict(left=m["left"] + round(x*m["width"]), top=m["top"] + round(y*m["height"]), width=round(w*m["width"]), height=round(h*m["height"]))
        return np.asarray(sct.grab(region))[:, :, :3].copy()


def read_image(path: str) -> np.ndarray:
    # imread does not reliably support Chinese paths on Windows.
    frame = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(tr("无法读取图片，请选择 PNG 或 JPG 截图"))
    return frame
