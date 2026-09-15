from app.tools.mysql_query import run_mysql_query
from app.tools.time_tool import get_current_time


def test_current_time_iso_like():
    value = get_current_time()
    assert "T" in value
    assert len(value) >= 19


def test_safe_sum_query_on_seed():
    raw = run_mysql_query(
        "SELECT SUM(amount) AS total FROM sales WHERE sale_date >= '2026-09-01' AND sale_date < '2026-10-01'"
    )
    assert "100000" in raw or "100000.0" in raw


def test_unknown_column_returns_error_string_not_raise():
    raw = run_mysql_query("SELECT SUM(amount) FROM sales WHERE order_date >= '2026-09-01'")
    assert "查询执行失败" in raw
    assert "sale_date" in raw
