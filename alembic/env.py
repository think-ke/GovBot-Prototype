from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from typing import List

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure app package is importable when running alembic from repo root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build SQLAlchemy URL for migrations
# Prefer a sync driver for Alembic even if app uses asyncpg
db_url = os.getenv("DATABASE_MIGRATIONS_URL") or os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost/govstackdb"
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", db_url)

# Import model metadata
from app.db.models.document import Base as DocumentBase
from app.db.models.webpage import Base as WebpageBase
from app.db.models.chat import Base as ChatBase
from app.db.models.chat_event import Base as ChatEventBase
from app.db.models.message_rating import Base as MessageRatingBase
from app.db.models.audit_log import Base as AuditBase
from app.db.models.transcription import Base as TranscriptionBase
# Import Collection model to register its table on the shared Base metadata
from app.db.models.collection import Collection  # noqa: F401

# Combine metadata objects for autogenerate (deduplicated)
_metadata_candidates: List = [
    DocumentBase.metadata,
    WebpageBase.metadata,
    ChatBase.metadata,
    ChatEventBase.metadata,
    MessageRatingBase.metadata,
    AuditBase.metadata,
    TranscriptionBase.metadata,
]
target_metadata_list: List = []
for md in _metadata_candidates:
    if md not in target_metadata_list:
        target_metadata_list.append(md)

# Alembic can accept a sequence of MetaData objects in target_metadata.
# We'll pass the list directly so autogenerate sees all models across modules.

def include_object(object, name, type_, reflected, compare_to):
    """
    Allow autogenerate to consider objects from all target metadatas.
    """
    # Always include objects defined in any of our metadata collections
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata_list,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),  # type: ignore[arg-type]
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata_list,
            compare_type=True,
            include_object=include_object,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
