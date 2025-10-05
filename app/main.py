from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, crud
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel
from typing import List, Optional

# --------------------------
# Create tables if they don't exist
# --------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Workout App API")

# --------------------------
# Dependency: DB session
# --------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# Pydantic models
# --------------------------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

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
    feedback: str  # "easy", "just right", "hard"

# --------------------------
# User endpoints
# --------------------------
@app.post("/users/", response_model=dict)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, user.name, user.email, user.password)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

# --------------------------
# Workout endpoints
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

@app.put("/workouts/{workout_id}", response_model=dict)
def update_workout_route(
    workout_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    default_sets: Optional[int] = None,
    default_reps: Optional[int] = None,
    default_load: Optional[float] = None,
    db: Session = Depends(get_db)
):
    workout = crud.update_workout(db, workout_id, name, description, default_sets, default_reps, default_load)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {
        "id": workout.id,
        "name": workout.name,
        "description": workout.description,
        "default_sets": workout.default_sets,
        "default_reps": workout.default_reps,
        "default_load": workout.default_load
    }

@app.delete("/workouts/{workout_id}", response_model=dict)
def delete_workout_route(workout_id: int, db: Session = Depends(get_db)):
    workout = crud.delete_workout(db, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"detail": "Workout deleted successfully"}

# --------------------------
# User log endpoints
# --------------------------
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
            "user": log.user.name,
            "workout": log.workout.name,
            "sets": log.sets,
            "reps": log.reps,
            "load": log.load,
            "feedback": log.feedback,
            "date": log.date.strftime("%Y-%m-%d %H:%M")
        }
        for log in logs
    ]

@app.put("/logs/{log_id}", response_model=dict)
def update_log_route(
    log_id: int,
    sets: Optional[int] = None,
    reps: Optional[int] = None,
    load: Optional[float] = None,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    log = crud.update_workout_log(db, log_id, sets, reps, load, feedback)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {
        "id": log.id,
        "user": log.user.name,
        "workout": log.workout.name,
        "sets": log.sets,
        "reps": log.reps,
        "load": log.load,
        "feedback": log.feedback,
        "date": log.date.strftime("%Y-%m-%d %H:%M")
    }

@app.delete("/logs/{log_id}", response_model=dict)
def delete_log_route(log_id: int, db: Session = Depends(get_db)):
    log = crud.delete_workout_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"detail": "Log deleted successfully"}

# --------------------------
# Root endpoint
# --------------------------
@app.get("/", response_model=dict)
def root():
    return {"message": "Workout app API is running!"}


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)