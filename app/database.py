from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote
from app.models import Base

# Your credentials
DB_USER = "postgres"
DB_PASSWORD = "P@risa*90"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "workoutdb"

# Encode special characters in password
DB_PASSWORD_ENCODED = quote(DB_PASSWORD)

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables (if not exists)
Base.metadata.create_all(bind=engine)

# Test connection
try:
    conn = engine.connect()
    print("Connected to PostgreSQL successfully!")
    conn.close()
except Exception as e:
    print("Error connecting to PostgreSQL:", e)
