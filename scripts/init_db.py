import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mysql import init_schema_and_seed


def main() -> None:
    init_schema_and_seed()
    print("schema and seed ready")


if __name__ == "__main__":
    main()
