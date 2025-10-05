# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, crud
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app and CORS once (do NOT redeclare app later)
app = FastAPI(title="Workout App API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (safe to run at startup)
Base.metadata.create_all(bind=engine)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True

class WorkoutCreate(BaseModel):
    name: str
    description: str
    default_sets: int
    default_reps: int
    default_load: float

class UserLogCreate(BaseModel):
    user_id: int
    workout_id: int
    sets: int
    reps: int
    load: float
    feedback: str

# --------------------------
# Users
# --------------------------
@app.post("/users/", response_model=dict)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, user.name, user.email, user.password)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

@app.get("/users/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

# --------------------------
# Workouts & logs (kept as you had them)
# --------------------------
@app.post("/workouts/", response_model=dict)
def create_workout(workout: WorkoutCreate, db: Session = Depends(get_db)):
    new_workout = crud.create_workout(
        db,
        name=workout.name,
        description=workout.description,
        default_sets=workout.default_sets,
        default_reps=workout.default_reps,
        default_load=workout.default_load
    )
    return {
        "id": new_workout.id,
        "name": new_workout.name,
        "description": new_workout.description,
        "default_sets": new_workout.default_sets,
        "default_reps": new_workout.default_reps,
        "default_load": new_workout.default_load
    }

@app.post("/user-logs/", response_model=dict)
def log_workout(log: UserLogCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == log.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    workout = db.query(models.Workout).filter(models.Workout.id == log.workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    new_log = crud.log_user_workout(
        db,
        user_id=log.user_id,
        workout_id=log.workout_id,
        sets=log.sets,
        reps=log.reps,
        load=log.load,
        feedback=log.feedback
    )
    return {
        "id": new_log.id,
        "user": user.name,
        "workout": workout.name,
        "sets": new_log.sets,
        "reps": new_log.reps,
        "load": new_log.load,
        "feedback": new_log.feedback,
        "date": new_log.date.strftime("%Y-%m-%d %H:%M")
    }

@app.get("/user-logs/{user_id}", response_model=List[dict])
def get_user_logs_route(user_id: int, db: Session = Depends(get_db)):
    logs = crud.get_user_logs(db, user_id=user_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this user")
    return [
        {
            "id": log.id,
            "user": getattr(log, "user", None).name if getattr(log, "user", None) else None,
            "workout": getattr(log, "workout", None).name if getattr(log, "workout", None) else None,
            "sets": log.sets,
            "reps": log.reps,
            "load": log.load,
            "feedback": log.feedback,
            "date": log.date.strftime("%Y-%m-%d %H:%M")
        }
        for log in logs
    ]

@app.get("/", response_model=dict)
def root():
    return {"message": "Workout app API is running!"}
