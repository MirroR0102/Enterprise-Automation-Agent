"""Delete agent_logs older than LOG_RETENTION_DAYS (default 60)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_service import purge_old_logs


def main() -> None:
    deleted = purge_old_logs()
    print(f"purged {deleted} log rows")


if __name__ == "__main__":
    main()
