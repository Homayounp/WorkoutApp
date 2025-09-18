from pydantic import BaseModel
from datetime import datetime


# --------------------------
# User schemas
# --------------------------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


# --------------------------
# Workout schemas
# --------------------------
class WorkoutCreate(BaseModel):
    name: str
    default_sets: int
    default_reps: int
    default_load: float

class WorkoutResponse(BaseModel):
    id: int
    name: str
    default_sets: int
    default_reps: int
    default_load: float

    class Config:
        orm_mode = True


# --------------------------
# User log schemas
# --------------------------
class UserLogCreate(BaseModel):
    user_id: int
    workout_id: int
    sets: int
    reps: int
    load: float
    feedback: str  # "easy", "just right", "hard"

class UserLogResponse(BaseModel):
    id: int
    user_id: int
    workout_id: int
    sets: int
    reps: int
    load: float
    feedback: str
    date: datetime

    class Config:
        orm_mode = True
