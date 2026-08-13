"""
JARVIS Database Connection Manager

Async SQLite connection management using SQLAlchemy async engine.
"""

import os
import shutil
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text

from app.db.models import Base

import structlog

logger = structlog.get_logger("jarvis.db")


class DatabaseManager:
    """Manages the async SQLite database connection and sessions."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Create engine, session factory, and ensure tables exist."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Run migrations
        await self._run_migrations()

        logger.info("database.initialized", url=self.database_url)

    async def _run_migrations(self) -> None:
        """Run any pending migrations. Uses a simple version tracking approach."""
        async with self.get_session() as session:
            # Ensure settings table has schema_version
            result = await session.execute(
                text("SELECT value FROM settings WHERE key = 'schema_version'")
            )
            row = result.fetchone()
            current_version = int(row[0]) if row else 0

            if current_version < 1:
                # Version 1: Initial schema (created by create_all above)
                await session.execute(
                    text(
                        "INSERT OR REPLACE INTO settings (key, value, type, description) "
                        "VALUES ('schema_version', '1', 'int', 'Database schema version')"
                    )
                )
                await session.execute(
                    text(
                        "INSERT OR IGNORE INTO settings (key, value, type, description) "
                        "VALUES ('setup_complete', 'false', 'bool', 'Whether initial setup is complete')"
                    )
                )
                await session.commit()
                logger.info("database.migration", version=1, status="applied")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def backup(self, backup_dir: str = "backups") -> str:
        """Create a database backup. Returns the backup file path."""
        os.makedirs(backup_dir, exist_ok=True)

        # Extract the database file path from the URL
        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"jarvis_backup_{timestamp}.db")

        # Use SQLite backup via raw connection
        async with self.engine.begin() as conn:
            # Checkpoint WAL to ensure all data is in main db file
            await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))

        shutil.copy2(db_path, backup_path)
        logger.info("database.backup", path=backup_path)
        return backup_path

    async def restore(self, backup_path: str) -> None:
        """Restore database from a backup file."""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")

        # Close current connections
        if self.engine:
            await self.engine.dispose()

        # Replace database file
        shutil.copy2(backup_path, db_path)

        # Reinitialize
        await self.initialize()
        logger.info("database.restored", from_backup=backup_path)

    async def get_stats(self) -> dict:
        """Get database statistics."""
        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
        size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        async with self.get_session() as session:
            tables = {}
            for table_name in Base.metadata.tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                tables[table_name] = result.scalar()

        return {
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "tables": tables,
        }

    async def close(self) -> None:
        """Close the database engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("database.closed")
