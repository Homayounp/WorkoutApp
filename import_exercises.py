# import_exercises.py
# Run once: python import_exercises.py
import csv
import os
import sys

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import Base, Exercise

# Ensure tables exist
Base.metadata.create_all(bind=engine)

CSV_PATH = os.path.join("app", "exercises.csv")

def import_exercises():
    db = SessionLocal()
    try:
        existing = db.query(Exercise).count()
        if existing > 0:
            print(f"[SKIP] Exercise table already has {existing} rows. Delete them first to re-import.")
            return

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                ex = Exercise(
                    name=row["name"].strip(),
                    body_part=row["bodyPart"].strip(),
                    equipment=row["equipment"].strip() if row.get("equipment") else None,
                    target=row["target"].strip(),
                )
                db.add(ex)
                count += 1

            db.commit()
            print(f"[OK] Imported {count} exercises.")
    finally:
        db.close()


if __name__ == "__main__":
    import_exercises()
