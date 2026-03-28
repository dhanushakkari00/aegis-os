from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["CLOUD_SQL_USE_CONNECTOR"] = "false"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GOOGLE_GENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["GMAIL_CLIENT_ID"] = ""
os.environ["GMAIL_CLIENT_SECRET"] = ""
os.environ["GMAIL_REFRESH_TOKEN"] = ""
os.environ["GMAIL_FROM_EMAIL"] = ""
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALLOW_DEMO_FALLBACK"] = "true"

from app.db.base import Base
from app.db.session import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
