"""
database/connection.py – Database connection manager using SQLAlchemy.
Supports SQLite, PostgreSQL, and MySQL via DATABASE_URL.
"""

from __future__ import annotations
import logging
from typing import Optional
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Thread-safe database connection manager."""

    _engine: Optional[Engine] = None
    _database_url: Optional[str] = None
    _db_type: Optional[str] = None

    @classmethod
    def connect(cls, database_url: str) -> None:
        """Create engine for the given DATABASE_URL."""
        kwargs: dict = {}

        if database_url.startswith("sqlite"):
            kwargs = {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
            cls._db_type = "sqlite"
        elif database_url.startswith("postgresql"):
            kwargs = {"pool_pre_ping": True, "pool_size": 5}
            cls._db_type = "postgresql"
        elif database_url.startswith("mysql"):
            kwargs = {"pool_pre_ping": True, "pool_size": 5}
            cls._db_type = "mysql"
        else:
            cls._db_type = "unknown"

        cls._engine = create_engine(database_url, **kwargs)
        cls._database_url = database_url

        # Enforce READ-ONLY for SQLite by listening to begin events
        if cls._db_type == "sqlite":
            @event.listens_for(cls._engine, "begin")
            def _on_begin(conn):  # noqa: ANN001
                pass  # read-only enforcement is done in sql_executor

        logger.info("Database connected: %s", cls._db_type)

    @classmethod
    def get_engine(cls) -> Engine:
        if cls._engine is None:
            raise RuntimeError("No database connected. Call DatabaseManager.connect() first.")
        return cls._engine

    @classmethod
    def test_connection(cls, database_url: str) -> tuple[bool, str]:
        """Test a connection without storing it."""
        try:
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return True, "Connection successful"
        except Exception as exc:
            logger.warning("Connection test failed: %s", exc)
            return False, str(exc)

    @classmethod
    def get_db_type(cls) -> str:
        return cls._db_type or "unknown"

    @classmethod
    def get_database_name(cls) -> str:
        if cls._database_url:
            url = cls._database_url
            if "sqlite" in url:
                return url.split("///")[-1].split("/")[-1]
            return url.split("/")[-1].split("?")[0]
        return "unknown"

    @classmethod
    def is_connected(cls) -> bool:
        if cls._engine is None:
            return False
        try:
            with cls._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @classmethod
    def dispose(cls) -> None:
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            cls._database_url = None
            cls._db_type = None
