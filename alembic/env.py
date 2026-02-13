# alembic/env.py
import sys
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# Add project root to path so "from app.xxx" works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import SQLALCHEMY_DATABASE_URL
from app.models import Base

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    connectable = create_engine(SQLALCHEMY_DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise NotImplementedError("Offline mode not configured.")
else:
    run_migrations_online()
