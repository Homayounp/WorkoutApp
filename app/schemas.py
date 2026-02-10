from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============== USER SCHEMAS ==============

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int  # user_id
    exp: datetime
    type: str  # "access" or "refresh"


# ============== EXERCISE SCHEMAS ==============

class ExerciseBase(BaseModel):
    id: str
    name: str
    body_part: str
    equipment: str
    gif_url: str
    target: str


class ExerciseResponse(ExerciseBase):
    class Config:
        from_attributes = True


# ============== WORKOUT SET SCHEMAS ==============

class WorkoutSetBase(BaseModel):
    exercise_id: str
    set_number: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None


class WorkoutSetCreate(WorkoutSetBase):
    pass


class WorkoutSetResponse(WorkoutSetBase):
    id: int
    session_id: int
    created_at: datetime
    exercise: Optional[ExerciseResponse] = None

    class Config:
        from_attributes = True


# ============== WORKOUT SESSION SCHEMAS ==============

class WorkoutSessionBase(BaseModel):
    name: str = "Workout"
    notes: Optional[str] = None


class WorkoutSessionCreate(WorkoutSessionBase):
    pass


class WorkoutSessionResponse(WorkoutSessionBase):
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    sets: List[WorkoutSetResponse] = []

    class Config:
        from_attributes = True


class WorkoutSessionUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    ended_at: Optional[datetime] = None
