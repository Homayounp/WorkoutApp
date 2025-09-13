# test_db.py
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:P%40risa%2A90@localhost:5432/workoutdb"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Connected!")
