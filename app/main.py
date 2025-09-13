from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, crud
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

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
@app.post("/users/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, user.name, user.email, user.password)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

# --------------------------
# Workout endpoints
# --------------------------
@app.post("/workouts/")
def create_workout(workout: WorkoutCreate, db: Session = Depends(get_db)):
    new_workout = crud.create_workout(
        db,
        name=workout.name,
        default_sets=workout.default_sets,
        default_reps=workout.default_reps,
        default_load=workout.default_load
    )
    return {
        "id": new_workout.id,
        "name": new_workout.name,
        "default_sets": new_workout.default_sets,
        "default_reps": new_workout.default_reps,
        "default_load": new_workout.default_load
    }

@app.put("/workouts/{workout_id}")
def update_workout_route(workout_id: int, name: str = None, default_sets: int = None, default_reps: int = None, default_load: float = None, db: Session = Depends(get_db)):
    workout = crud.update_workout(db, workout_id, name, default_sets, default_reps, default_load)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@app.delete("/workouts/{workout_id}")
def delete_workout_route(workout_id: int, db: Session = Depends(get_db)):
    workout = crud.delete_workout(db, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"detail": "Workout deleted successfully"}

# --------------------------
# User log endpoints
# --------------------------
@app.post("/user-logs/")
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

@app.get("/user-logs/{user_id}")
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

@app.put("/logs/{log_id}")
def update_log_route(log_id: int, sets: int = None, reps: int = None, load: float = None, feedback: str = None, db: Session = Depends(get_db)):
    log = crud.update_workout_log(db, log_id, sets, reps, load, feedback)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@app.delete("/logs/{log_id}")
def delete_log_route(log_id: int, db: Session = Depends(get_db)):
    log = crud.delete_workout_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"detail": "Log deleted successfully"}

@app.get("/")
def root():
    return {"message": "Workout app API is running!"}
