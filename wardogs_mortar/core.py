"""Pure coordinate geometry and versioned, flat-ground L81 firing tables."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __post_init__(self):
        if not all(math.isfinite(n) for n in (self.x, self.y)):
            raise ValueError("坐标必须是有限数字")

    def label(self) -> str:
        return f"X {self.x:.2f}   Y {self.y:.2f}"


@dataclass(frozen=True)
class Solution:
    distance: float
    bearing: float | None
    mil: float | None
    status: str


@lru_cache(maxsize=1)
def firing_data() -> dict:
    path = Path(__file__).parent / "data" / "l81.json"
    return json.loads(path.read_text(encoding="utf-8"))


def elevation(distance: float) -> float | None:
    data = firing_data()
    if not math.isfinite(distance) or not data["min_range_m"] - 1e-6 <= distance <= data["max_range_m"] + 1e-6:
        return None
    distance = min(data["max_range_m"], max(data["min_range_m"], distance))
    table = data["table"]
    for (da, ma), (db, mb) in zip(table, table[1:]):
        if da <= distance <= db:
            return ma + (distance - da) / (db - da) * (mb - ma)
    return None


def calculate(origin: Point, target: Point) -> Solution:
    dx, dy = target.x - origin.x, target.y - origin.y
    distance = math.hypot(dx, dy) * 100
    bearing = math.degrees(math.atan2(dx, dy)) % 360 if distance else None
    mil = elevation(distance)
    data = firing_data()
    status = "射程内"
    if distance == 0:
        status = "两点重合，方位角无定义"
    elif distance < data["min_range_m"] - 1e-6:
        status = f"距离过近 · 最小 {data['min_range_m']} m"
    elif distance > data["max_range_m"] + 1e-6:
        status = f"超出射程 · 最大 {data['max_range_m']} m"
    return Solution(distance, bearing, mil, status)


def bearing_text(value: float | None) -> str:
    return "—" if value is None else f"{round(value, 1) % 360:05.1f}°"
