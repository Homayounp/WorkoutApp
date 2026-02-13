# nuke_db.py
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # Drop all tables (CASCADE handles foreign keys)
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    conn.commit()
    print("💥 All tables dropped! Database is completely clean.")
