from fastapi import FastAPI
from database import Base, engine
import models

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Workout App running with PostgreSQL!"}
