from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.enterprise.config import enterprise_settings
from backend.enterprise.databases import InventoryBase
from backend.enterprise import models  # noqa: F401


def _escape_configparser_percent(value: str) -> str:
    """Escape percent signs before writing URLs into Alembic ConfigParser.

    MySQL passwords often contain special characters. For example, the password
    `FinmarkApp@2026!` becomes `FinmarkApp%402026!` inside a SQLAlchemy URL.
    Alembic stores sqlalchemy.url in Python configparser, where `%` is treated
    as interpolation syntax. Doubling `%` keeps the real URL unchanged after
    configparser reads it, while preventing `invalid interpolation syntax`.
    """
    return value.replace("%", "%%")


DATABASE_URL = enterprise_settings.inventory_database_url
config = context.config
config.set_main_option("sqlalchemy.url", _escape_configparser_percent(DATABASE_URL))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = InventoryBase.metadata


def run_migrations_offline():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
