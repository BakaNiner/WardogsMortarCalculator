"""Reproducible OCR acceptance report against the supplied screenshots."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wardogs_mortar.capture import crop_region, read_image
from wardogs_mortar.ocr import CoordinateReader

reader = CoordinateReader()
report = []
for path in sorted((Path(__file__).resolve().parents[1] / "screenshots").glob("*.jpg")):
    result = reader.read(crop_region(read_image(str(path))))
    report.append(dict(file=path.name, x=result.point.x, y=result.point.y, confidence=round(result.confidence, 5), seconds=round(result.elapsed, 3), text=result.raw))
print(json.dumps(report, ensure_ascii=False, indent=2))

