"""
Alembic migration environment.

- The database URL comes from DATABASE_URL (app.config), the same
  setting the API uses, so there is one source of truth.
- target_metadata is the app's Base.metadata with every model imported,
  so `alembic revision --autogenerate` can see all tables.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app import models  # noqa: F401  (registers every table on Base.metadata)
from app.config import settings
from app.database import Base

config = context.config

# A caller (e.g. the test suite) may pass a URL explicitly;
# otherwise use DATABASE_URL.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option(
        "sqlalchemy.url",
        settings.database_url.replace("%", "%%"),
    )

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without a DB connection (`alembic upgrade head --sql`)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
