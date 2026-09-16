"""报告文件读写：reports 目录内 roundtrip 与路径穿越防护。"""

from pathlib import Path

import pytest

from app.tools.file_io import read_report, write_report


def test_write_and_read_roundtrip(tmp_path, monkeypatch):
    """write_report 写入后 read_report 应读回相同内容。"""
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    msg = write_report("weekly.md", "# hi")
    assert "weekly.md" in msg
    assert read_report("weekly.md") == "# hi"
    get_settings.cache_clear()


def test_rejects_parent_traversal():
    """../ 路径穿越应被拒绝。"""
    with pytest.raises(ValueError):
        write_report("../secret.md", "nope")


def test_rejects_absolute_path():
    """绝对路径写入应被拒绝。"""
    with pytest.raises(ValueError):
        write_report(str(Path.cwd() / "x.md"), "nope")
