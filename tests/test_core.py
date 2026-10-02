import math

import pytest

from wardogs_mortar.core import Point, bearing_text, calculate, elevation, firing_data


@pytest.mark.parametrize("target,expected", [(Point(0, 1), 0), (Point(1, 0), 90), (Point(0, -1), 180), (Point(-1, 0), 270), (Point(-1, 1), 315)])
def test_compass_axes(target, expected):
    assert calculate(Point(0, 0), target).bearing == expected


def test_screenshot_pair():
    result = calculate(Point(96.8, 113.29), Point(97.41, 107.37))
    assert result.distance == pytest.approx(595.1344386)
    assert result.bearing == pytest.approx(174.116974)
    assert result.mil == pytest.approx(323.109269)


def test_range_boundaries_and_interpolation():
    assert elevation(131.99) is None
    assert elevation(132) == 850
    assert elevation(684) == 150
    assert elevation(684.01) is None
    assert elevation(500) == pytest.approx(461.428571)
    assert elevation(math.nan) is None


def test_table_is_ordered_and_has_valid_samples():
    rows = firing_data()["table"]
    assert rows[0] == [132, 850]
    assert rows[-1] == [684, 150]
    assert all(a[0] < b[0] and a[1] > b[1] for a, b in zip(rows, rows[1:]))


def test_same_point_has_no_bearing_or_mil():
    result = calculate(Point(1, 1), Point(1, 1))
    assert result.distance == 0
    assert result.bearing is None
    assert result.mil is None


def test_coordinate_subtraction_roundoff_at_range_limits():
    assert calculate(Point(80, 80), Point(81.32, 80)).mil == 850
    assert calculate(Point(80, 80), Point(86.84, 80)).mil == 150


def test_display_wraps_rounded_north():
    assert bearing_text(359.99) == "000.0°"


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_invalid_point(value):
    with pytest.raises(ValueError):
        Point(value, 0)
