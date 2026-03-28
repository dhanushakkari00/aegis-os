from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_matches_current_models(tmp_path) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    database_path = tmp_path / "alembic-smoke.db"
    database_url = f"sqlite:///{database_path}"

    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["DATABASE_URL"] = database_url
    env["SECRET_KEY"] = "migration-test-secret"
    env["GOOGLE_GENAI_API_KEY"] = ""
    env["GEMINI_API_KEY"] = ""

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {"users", "cases", "analysis_runs", "artifacts", "recommended_actions"}.issubset(
        set(inspector.get_table_names())
    )
    case_columns = {column["name"] for column in inspector.get_columns("cases")}
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    assert "owner_id" in case_columns
    assert {"email", "username", "hashed_password"}.issubset(user_columns)
