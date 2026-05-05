from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import app.models  # noqa: F401 - ensures all models are registered with Base.metadata
from app.core.config import get_settings
from app.db.base import Base

# Alembic Config object — provides access to values in the .ini file.
config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_uri)

# Set up Python logging from the alembic.ini config.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata for autogenerate support.
target_metadata = Base.metadata

# Alembic 1.18.x autogenerate options:
# - compare_type: detect column type changes.
# - compare_server_default: detect server-side default changes.
# - include_schemas: inspect all schemas (useful for multi-schema setups).
AUTOGENERATE_OPTIONS = {
    "compare_type": True,
    "compare_server_default": True,
}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL (no live DB connection needed).
    Calls to context.execute() emit the given string to script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **AUTOGENERATE_OPTIONS,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the migration context.
    Uses NullPool to avoid connection reuse issues in migration scripts.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **AUTOGENERATE_OPTIONS,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
