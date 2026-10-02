"""Local OCR plus strict, label-aware coordinate extraction."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import time

import cv2
import numpy as np

from .core import Point
from .i18n import tr


COORDINATE = re.compile(r"(?<![a-z0-9])([xy])\s*[:=]?\s*(\d{1,3}[.,]\d{2})(?![\w.,])", re.I)


class RecognitionError(ValueError):
    pass


@dataclass(frozen=True)
class TextRegion:
    text: str
    score: float
    box: tuple[tuple[float, float], ...]


@dataclass
class Recognition:
    point: Point
    confidence: float
    elapsed: float
    preview: np.ndarray
    raw: str


def extract_coordinates(regions: list[TextRegion], threshold: float = .80) -> tuple[Point, float]:
    axes: dict[str, list] = {"x": [], "y": []}
    for region in regions:
        if region.score < threshold:
            continue
        # OCR sometimes inserts spaces inside a decimal number.
        text = re.sub(r"(?<=\d)\s+(?=[\d.,])|(?<=[.,])\s+(?=\d)", "", region.text)
        for match in COORDINATE.finditer(text):
            axes[match[1].lower()].append((float(match[2].replace(",", ".")), region))
    if not axes["x"] or not axes["y"]:
        raise RecognitionError(tr("未找到完整且清晰的 X/Y 坐标。请打开地图，让坐标文字完整显示后重试。"))
    pairs = []
    for x, xr in axes["x"]:
        for y, yr in axes["y"]:
            xpts, ypts = np.array(xr.box), np.array(yr.box)
            xc, yc = xpts.mean(axis=0), ypts.mean(axis=0)
            height = max(np.ptp(xpts[:, 1]), np.ptp(ypts[:, 1]), 1)
            # On the map, Y is above X near the same crosshair. Also permit a
            # single text line with both labeled coordinates (imported crops).
            if abs(xc[0]-yc[0]) > height*12 or not -height*2 <= xc[1]-yc[1] <= height*10:
                continue
            pairs.append((Point(x, y), min(xr.score, yr.score)))
    unique = {p: score for p, score in pairs}
    if not unique:
        raise RecognitionError(tr("X/Y 文字位置不匹配，请重新框选地图区域。"))
    if len(unique) != 1:
        raise RecognitionError(tr("发现多组坐标，无法确定当前选点。请缩小识别区域后重试。"))
    return next(iter(unique.items()))


class CoordinateReader:
    def __init__(self):
        import rapidocr
        from rapidocr import RapidOCR
        models = Path(rapidocr.__file__).parent / "models"
        files = {"Det": "PP-OCRv6_det_small.onnx", "Rec": "PP-OCRv6_rec_small.onnx", "Cls": "ch_ppocr_mobile_v2.0_cls_mobile.onnx"}
        for filename in files.values():
            if not (models / filename).is_file():
                raise RecognitionError(tr("本地 OCR 模型缺失，请保留完整程序目录并重新解压。缺失文件：{filename}", filename=filename))
        self.engine = RapidOCR(params={
            "Global.log_level": "error",
            "EngineConfig.onnxruntime.intra_op_num_threads": 2,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            **{f"{part}.model_path": str(models / filename) for part, filename in files.items()},
        })

    def read(self, image: np.ndarray) -> Recognition:
        start = time.perf_counter()
        if image is None or image.size == 0:
            raise RecognitionError(tr("截图为空，请检查显示器与识别区域"))
        if image.std() < 2:
            raise RecognitionError(tr("截图没有可识别内容，请尝试游戏无边框窗口模式"))
        h, w = image.shape[:2]
        # Preserve small HUD text; the detector's own resizing is controlled below.
        scale = min(2.0, 1800 / max(h, w))
        enlarged = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        result = self.engine(enlarged, use_cls=False)
        regions = []
        if result.txts is not None:
            for text, score, box in zip(result.txts, result.scores, result.boxes):
                regions.append(TextRegion(text, float(score), tuple(tuple(float(v)/scale for v in pt) for pt in box)))
        point, confidence = extract_coordinates(regions)
        preview = image.copy()
        for region in regions:
            if COORDINATE.search(region.text):
                cv2.polylines(preview, [np.array(region.box, dtype=np.int32)], True, (110, 220, 80), 2)
        return Recognition(point, confidence, time.perf_counter()-start, preview, " | ".join(r.text for r in regions))
