"""初始化业务主库 schema 与演示种子数据。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mysql import init_schema_and_seed


def main() -> None:
    """执行建表与 seed，适用于 mock SQLite 或 MySQL。"""
    init_schema_and_seed()
    print("schema and seed ready")


if __name__ == "__main__":
    main()
