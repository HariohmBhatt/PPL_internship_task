"""Alembic migration environment."""

import os
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic config
config = context.config


def _coerce_db_url(url: str) -> str:
    """Normalize DATABASE_URL to use psycopg3 driver and correct scheme."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Set SQLAlchemy URL (prefer env, else coerce existing)
env_url = os.getenv("DATABASE_URL", "")
if env_url:
    config.set_main_option("sqlalchemy.url", _coerce_db_url(env_url))
else:
    current = config.get_main_option("sqlalchemy.url") or ""
    if current:
        config.set_main_option("sqlalchemy.url", _coerce_db_url(current))


# Import models for metadata
from app.models import Base  # noqa: E402

# Target metadata for autogenerate
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with database connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously."""
    section = config.get_section(config.config_ini_section, {})
    # Ensure URL uses psycopg3 even if alembic.ini provided plain postgres
    if "sqlalchemy.url" in section:
        section["sqlalchemy.url"] = _coerce_db_url(section["sqlalchemy.url"])  # type: ignore[index]

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
