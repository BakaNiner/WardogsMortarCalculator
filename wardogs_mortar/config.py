from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path


DEFAULT_ROI = (0.325, 0.19, 0.35, 0.62)


def data_dir() -> Path:
    root = Path(os.environ.get("WARDOGS_CONFIG_DIR", Path(os.environ.get("LOCALAPPDATA", Path.home())) / "WardogsMortar"))
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass
class Settings:
    origin_hotkey: str = "F1"
    target_hotkey: str = "F2"
    overlay_hotkey: str = "F3"
    monitor: int = 1
    roi: list[float] = field(default_factory=lambda: list(DEFAULT_ROI))
    overlay_opacity: int = 92
    overlay_visible: bool = True
    overlay_position: list[int] | None = None
    sound: bool = True

    @classmethod
    def load(cls) -> "Settings":
        try:
            raw = json.loads((data_dir() / "settings.json").read_text(encoding="utf-8"))
            obj = cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})
            if not isinstance(obj.monitor, int) or obj.monitor < 1:
                raise ValueError("Invalid monitor")
            if not valid_roi(obj.roi):
                raise ValueError("Invalid region")
            if not isinstance(obj.overlay_opacity, int) or not 35 <= obj.overlay_opacity <= 100:
                raise ValueError("Invalid opacity")
            for key in (obj.origin_hotkey, obj.target_hotkey, obj.overlay_hotkey):
                if not isinstance(key, str) or not key:
                    raise ValueError("Invalid hotkey")
            if obj.overlay_position is not None and (len(obj.overlay_position) != 2 or not all(isinstance(v, int) for v in obj.overlay_position)):
                raise ValueError("Invalid position")
            return obj
        except (OSError, ValueError, TypeError, AttributeError):
            return cls()

    def save(self):
        path = data_dir() / "settings.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


def valid_roi(roi) -> bool:
    try:
        x, y, w, h = roi
        return all(isinstance(v, (float, int)) for v in roi) and 0 <= x < 1 and 0 <= y < 1 and w >= .03 and h >= .03 and x + w <= 1.000001 and y + h <= 1.000001
    except (ValueError, TypeError):
        return False

