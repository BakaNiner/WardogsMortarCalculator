from pathlib import Path

import cv2
import numpy as np
import pytest

from wardogs_mortar.capture import crop_region, read_image
from wardogs_mortar.core import Point
from wardogs_mortar.ocr import CoordinateReader, RecognitionError, TextRegion, extract_coordinates


def region(text, y=70, x=30, score=.99):
    return TextRegion(text, score, ((x, y), (x+80, y), (x+80, y+20), (x, y+20)))


def test_labels_override_ocr_reading_order():
    point, _ = extract_coordinates([region("y113.29", 10), region("x96.80", 70)])
    assert point == Point(96.80, 113.29)


def test_labeled_line_and_decimal_comma():
    assert extract_coordinates([region("X:96,80 Y:113,29")])[0] == Point(96.80, 113.29)


@pytest.mark.parametrize("text", ["x9680", "x96.8", "x96.800", "x96.8O", "x96.80O", "96.80", "x-96.80", "x1968.00"])
def test_uncertain_numeric_values_are_rejected(text):
    with pytest.raises(RecognitionError):
        extract_coordinates([region(text), region("y113.29", 10)])


def test_low_confidence_rejected():
    with pytest.raises(RecognitionError):
        extract_coordinates([region("x96.80", score=.5), region("y113.29", 10)])


def test_ambiguous_or_separated_values_are_rejected():
    with pytest.raises(RecognitionError):
        extract_coordinates([region("x96.80"), region("x97.41"), region("y113.29", 10)])
    with pytest.raises(RecognitionError):
        extract_coordinates([region("x96.80", x=700), region("y113.29", 10)])


@pytest.fixture(scope="module")
def reader():
    return CoordinateReader()


@pytest.mark.parametrize("name,point", [
    ("x 71.82 y 56.35.jpg", Point(71.82, 56.35)),
    ("x 96.80 y 113.29.jpg", Point(96.80, 113.29)),
    ("x 97.41 y 107.37.jpg", Point(97.41, 107.37)),
])
@pytest.mark.parametrize("width", [2560, 1920, 1280])
def test_real_screenshots(reader, name, point, width):
    path = Path(__file__).resolve().parents[1] / "screenshots" / name
    image = read_image(str(path))
    if width != image.shape[1]:
        image = cv2.resize(image, (width, round(image.shape[0]*width/image.shape[1])), interpolation=cv2.INTER_AREA)
    result = reader.read(crop_region(image))
    assert result.point == point


def test_blank_frame_does_not_overwrite(reader):
    with pytest.raises(RecognitionError):
        reader.read(np.zeros((500, 500, 3), dtype=np.uint8))
