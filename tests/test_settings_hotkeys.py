import pytest

from wardogs_mortar.config import Settings, valid_roi
from wardogs_mortar.win32 import parse_hotkey


def test_hotkey_parser():
    assert parse_hotkey("F1") == (0x4000, 0x70)
    assert parse_hotkey("Ctrl+Alt+K") == (0x4003, ord("K"))
    assert parse_hotkey("F24") == (0x4000, 0x87)


@pytest.mark.parametrize("key", ["F12", "F25", "Win+X", "Ctrl+Ctrl+A", "", "A", "Ctrl+"])
def test_invalid_hotkeys(key):
    with pytest.raises(ValueError):
        parse_hotkey(key)


def test_settings_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("WARDOGS_CONFIG_DIR", str(tmp_path))
    settings = Settings(origin_hotkey="Ctrl+F1", roi=[.2, .2, .5, .6])
    settings.save()
    assert Settings.load() == settings
    (tmp_path / "settings.json").write_text('{"roi": [1, 2]}')
    assert Settings.load() == Settings()


@pytest.mark.parametrize("roi", [[0, 0, 0, 1], [-1, 0, .5, .5], [.8, 0, .5, .5], None, [0, 0, .5]])
def test_bad_regions(roi):
    assert not valid_roi(roi)

