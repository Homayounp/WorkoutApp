import sys
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from urllib.parse import quote

# Add app folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Base  # Base from models.py

# Alembic config
config = context.config
fileConfig(config.config_file_name)

# Database credentials
DB_USER = "postgres"
DB_PASSWORD = "P@risa*90"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "workoutdb"

DB_PASSWORD_ENCODED = quote(DB_PASSWORD)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Target metadata for 'autogenerate'
target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# Run migrations
if context.is_offline_mode():
    raise NotImplementedError("Offline mode not configured.")
else:
    run_migrations_online()
