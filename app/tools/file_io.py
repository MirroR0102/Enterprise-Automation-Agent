from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from app.config import reports_path


def _safe_report_path(filename: str) -> Path:
    name = (filename or "").strip()
    if not name:
        raise ValueError("文件名不能为空")
    if Path(name).is_absolute() or ":" in name.replace("://", ""):
        raise ValueError("禁止绝对路径")
    parts = Path(name).parts
    if any(part == ".." for part in parts):
        raise ValueError("禁止路径穿越")
    root = reports_path().resolve()
    target = (root / name).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("文件必须位于 reports/ 目录内") from exc
    if target.suffix.lower() != ".md":
        raise ValueError("只允许读写 .md 文件")
    return target


def write_report(filename: str, content: str) -> str:
    path = _safe_report_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"已写入 {path.name}（{len(content)} 字符）"


def read_report(filename: str) -> str:
    path = _safe_report_path(filename)
    if not path.exists():
        return f"文件不存在: {path.name}"
    return path.read_text(encoding="utf-8")


@tool
def write_markdown_report(filename: str, content: str) -> str:
    """把 Markdown 报告写入 reports/ 目录。filename 只能是相对文件名，例如 weekly.md。"""
    try:
        return write_report(filename, content)
    except ValueError as exc:
        return f"写入失败: {exc}"


@tool
def read_markdown_report(filename: str) -> str:
    """读取 reports/ 下的 Markdown 报告。"""
    try:
        return read_report(filename)
    except ValueError as exc:
        return f"读取失败: {exc}"
