# reset_db.py
from sqlalchemy import create_engine
from app.models import Base
from urllib.parse import quote

# Database credentials (must match app/database.py)
DB_USER = "postgres"
DB_PASSWORD = "P@risa*90"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "workoutdb"

DB_PASSWORD_ENCODED = quote(DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def reset_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("✅ Recreating all tables...")
    Base.metadata.create_all(bind=engine)

    print("🎉 Database reset complete!")

if __name__ == "__main__":
    reset_database()
