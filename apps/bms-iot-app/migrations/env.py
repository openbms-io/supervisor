import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from sqlmodel import SQLModel
from src.config.settings import settings

# Add project root to Python path for package imports
# This migrations file is in apps/bms-iot-app/migrations/env.py
# We need to add the monorepo root (../../ from here) to access packages/
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Use database URL from centralized settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support

# Import SQLModel models for Alembic migration coverage
try:
    # Core models managed by Alembic
    from src.models.controller_points import ControllerPointsModel
    from src.models.iot_device_status import IotDeviceStatusModel
    from src.models.deployment_config import DeploymentConfigModel

    # BACnet config models - now that MQTT dependency issues are resolved
    from src.models.bacnet_config import BacnetConfigModel, BacnetReaderConfigModel

    print("Successfully imported all models for Alembic migrations")
    print(
        "Models imported:",
        ControllerPointsModel.__name__,
        IotDeviceStatusModel.__name__,
        DeploymentConfigModel.__name__,
        BacnetConfigModel.__name__,
        BacnetReaderConfigModel.__name__,
    )

except ImportError as e:
    print(f"Warning: Could not import some models: {e}")
    import traceback

    traceback.print_exc()

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
