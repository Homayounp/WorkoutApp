from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, crud
from app.database import engine, SessionLocal, Base
from pydantic import BaseModel

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for user input
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

# Route: register user
@app.post("/users/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, user.name, user.email, user.password)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}


# Pydantic model for creating a workout
class WorkoutCreate(BaseModel):
    name: str
    default_sets: int
    default_reps: int
    default_load: float

# Route: add a workout template
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


# Pydantic model for logging a user workout
class UserLogCreate(BaseModel):
    user_id: int
    workout_id: int
    sets: int
    reps: int
    load: float
    feedback: str  # e.g., "easy", "just right", "hard"

# Route: log a user workout
@app.post("/user-logs/")
def log_workout(log: UserLogCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = crud.get_user_by_email(db, db.query(models.User).filter(models.User.id==log.user_id).first().email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
        "user_id": new_log.user_id,
        "workout_id": new_log.workout_id,
        "sets": new_log.sets,
        "reps": new_log.reps,
        "load": new_log.load,
        "feedback": new_log.feedback,
        "date": new_log.date
    }

# Route: get all logs for a user
@app.get("/user-logs/{user_id}")
def get_user_logs_route(user_id: int, db: Session = Depends(get_db)):
    logs = crud.get_user_logs(db, user_id=user_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this user")
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "workout_id": log.workout_id,
            "sets": log.sets,
            "reps": log.reps,
            "load": log.load,
            "feedback": log.feedback,
            "date": log.date
        }
        for log in logs
    ]
