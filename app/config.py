# app/config.py
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

# ── Database ──────────────────────────────────────────
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "P@risa*90")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "workoutdb")

DB_PASSWORD_ENCODED = quote(DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ── JWT ───────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
