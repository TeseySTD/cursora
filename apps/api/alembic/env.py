"""Async Alembic environment.

The URL comes from application settings; metadata comes from the shared
DeclarativeBase. Every module's ``models`` is imported so that
``alembic revision --autogenerate`` sees all tables.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from cursora_api.core.config import get_settings
from cursora_api.core.db import Base
from cursora_api.modules.gate import models as _gate_models  # noqa: F401
from cursora_api.modules.insights import models as _insights_models  # noqa: F401
from cursora_api.modules.risk import models as _risk_models  # noqa: F401
from cursora_api.modules.sessions import models as _sessions_models  # noqa: F401
from cursora_api.modules.tenant import models as _tenant_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
