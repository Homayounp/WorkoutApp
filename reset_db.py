# reset_db.py
from sqlalchemy import create_engine
from app.database import Base, DATABASE_URL
from alembic import command
from alembic.config import Config

def reset_database():
    engine = create_engine(DATABASE_URL)

    # Drop all tables
    print("⚠️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    # Run Alembic migrations
    print("✅ Tables dropped. Recreating schema...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    print("🎉 Database reset and migrated to latest version!")

if __name__ == "__main__":
    reset_database()
