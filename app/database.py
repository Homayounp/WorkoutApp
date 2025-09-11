from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:P%40risa%2A90@localhost:5432/workoutdb"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Test connection
try:
    conn = engine.connect()
    print("Connected to PostgreSQL successfully!")
    conn.close()
except Exception as e:
    print("Error connecting to PostgreSQL:", e)
