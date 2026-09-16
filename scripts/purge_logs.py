"""清理超过 LOG_RETENTION_DAYS（默认 60 天）的 agent_logs 记录。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_service import purge_old_logs


def main() -> None:
    """删除过期日志并打印删除行数。"""
    deleted = purge_old_logs()
    print(f"purged {deleted} log rows")


if __name__ == "__main__":
    main()
