from pathlib import Path

import pytest

from app.tools.file_io import read_report, write_report


def test_write_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    msg = write_report("weekly.md", "# hi")
    assert "weekly.md" in msg
    assert read_report("weekly.md") == "# hi"
    get_settings.cache_clear()


def test_rejects_parent_traversal():
    with pytest.raises(ValueError):
        write_report("../secret.md", "nope")


def test_rejects_absolute_path():
    with pytest.raises(ValueError):
        write_report(str(Path.cwd() / "x.md"), "nope")
