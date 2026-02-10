from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from contextlib import asynccontextmanager

from database import engine, Base, get_db
from models import User
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    ExerciseResponse,
    WorkoutSessionCreate, WorkoutSessionResponse,
    WorkoutSetCreate, WorkoutSetResponse
)
from dependencies import get_current_user
from auth import create_tokens, decode_token
import crud
from utils import load_exercises_from_csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup: Create tables and load exercises
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Load exercises from CSV
    async for db in get_db():
        await load_exercises_from_csv(db, "exercises.csv")
        break
    
    yield
    
    # Shutdown: cleanup if needed
    await engine.dispose()


app = FastAPI(
    title="WorkoutApp API",
    description="A fitness tracking application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== AUTH ROUTES ==============

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    if await crud.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username exists
    if await crud.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user = await crud.create_user(db, user_data)
    return user


@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT tokens."""
    user = await crud.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return create_tokens(user.id)


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Get new tokens using a refresh token."""
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = int(payload.get("sub"))
    user = await crud.get_user_by_id(db, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return create_tokens(user.id)


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user


# ============== EXERCISE ROUTES ==============

@app.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    body_part: Optional[str] = None,
    target: Optional[str] = None,
    equipment: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get exercises with optional filtering."""
    exercises = await crud.get_exercises(
        db, skip=skip, limit=limit,
        body_part=body_part, target=target,
        equipment=equipment, search=search
    )
    return exercises


@app.get("/exercises/body-parts", response_model=List[str])
async def get_body_parts(db: AsyncSession = Depends(get_db)):
    """Get all available body parts."""
    return await crud.get_body_parts(db)


@app.get("/exercises/targets", response_model=List[str])
async def get_targets(db: AsyncSession = Depends(get_db)):
    """Get all available target muscles."""
    return await crud.get_targets(db)


@app.get("/exercises/equipment", response_model=List[str])
async def get_equipment(db: AsyncSession = Depends(get_db)):
    """Get all available equipment types."""
    return await crud.get_equipment(db)


@app.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific exercise by ID."""
    exercise = await crud.get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    return exercise


# ============== WORKOUT SESSION ROUTES (PROTECTED) ==============

@app.post("/workouts", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    session_data: WorkoutSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workout session."""
    session = await crud.create_workout_session(db, current_user.id, session_data)
    return session


@app.get("/workouts", response_model=List[WorkoutSessionResponse])
async def get_workouts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all workout sessions for the current user."""
    sessions = await crud.get_workout_sessions(db, current_user.id, skip, limit)
    return sessions


@app.get("/workouts/{workout_id}", response_model=WorkoutSessionResponse)
async def get_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workout session."""
    session = await crud.get_workout_session(db, workout_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return session


@app.patch("/workouts/{workout_id}/end", response_model=WorkoutSessionResponse)
async def end_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a workout session as ended."""
    session = await crud.end_workout_session(db, workout_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return session


@app.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workout session."""
    deleted = await crud.delete_workout_session(db, workout_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )


# ============== WORKOUT SET ROUTES (PROTECTED) ==============

@app.post("/workouts/{workout_id}/sets", response_model=WorkoutSetResponse, status_code=status.HTTP_201_CREATED)
async def add_set(
    workout_id: int,
    set_data: WorkoutSetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a set to a workout session."""
    workout_set = await crud.add_set_to_session(db, workout_id, current_user.id, set_data)
    if not workout_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return workout_set


@app.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workout set."""
    deleted = await crud.delete_workout_set(db, set_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )


# ============== HEALTH CHECK ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}