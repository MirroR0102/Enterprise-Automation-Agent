from app.tools.mysql_query import is_safe_select_sql


def test_drop_table_rejected():
    assert is_safe_select_sql("DROP TABLE sales") is False


def test_delete_rejected():
    assert is_safe_select_sql("delete from sales") is False


def test_alter_rejected():
    assert is_safe_select_sql("ALTER TABLE sales ADD COLUMN x INT") is False


def test_multi_statement_rejected():
    assert is_safe_select_sql("SELECT 1; DROP TABLE users") is False


def test_insert_rejected():
    assert is_safe_select_sql("INSERT INTO sales VALUES (1, '2026-09-01', 1, 'x')") is False


def test_valid_select_allowed():
    sql = "SELECT SUM(amount) FROM sales WHERE sale_date >= '2026-09-01' AND sale_date < '2026-10-01'"
    assert is_safe_select_sql(sql) is True
