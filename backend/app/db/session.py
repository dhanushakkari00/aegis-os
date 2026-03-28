from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def create_sqlalchemy_engine() -> Engine:
    if settings.cloud_sql_use_connector and settings.cloud_sql_connection_name:
        try:
            from google.cloud.sql.connector import Connector, IPTypes
        except ImportError as exc:
            raise RuntimeError("Cloud SQL connector dependency is unavailable.") from exc

        connector = Connector(refresh_strategy="lazy")

        def getconn():
            return connector.connect(
                settings.cloud_sql_connection_name,
                "psycopg",
                user=settings.postgres_user,
                password=settings.postgres_password,
                db=settings.postgres_db,
                ip_type=IPTypes.PUBLIC,
            )

        return create_engine(
            "postgresql+psycopg://",
            creator=getconn,
            future=True,
            pool_pre_ping=True,
        )

    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = create_sqlalchemy_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
