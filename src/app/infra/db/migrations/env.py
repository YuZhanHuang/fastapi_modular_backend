from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.infra.db.base import Base
from app.infra.db import models  # noqa: F401  # 確保所有 models 被載入


# 這是 Alembic 的 config 物件，對應 alembic.ini
config = context.config

# 設定 sqlalchemy.url，優先使用我們的 settings.DATABASE_URL
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 啟用 logging（可選）
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        # 沒有 [formatters]/[handlers]/[loggers] 就不啟用 logging 設定
        pass

# 告訴 Alembic 我們的 metadata 在哪，用來自動比對 schema
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

