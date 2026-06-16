import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "test_finmark.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("SEED_DEMO_DATA", "true")
os.environ.setdefault("DATABASE_ECHO", "false")

from backend.database import init_db, session_scope  # noqa: E402
from backend.services.seed_service import seed_database  # noqa: E402

init_db()
with session_scope() as db:
    seed_database(db)
