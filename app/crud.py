from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from models import User, Exercise, WorkoutSession, WorkoutSet
from schemas import UserCreate, WorkoutSessionCreate, WorkoutSetCreate
from auth import get_password_hash, verify_password


# ============== USER CRUD ==============

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ============== EXERCISE CRUD ==============

async def get_exercises(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    body_part: Optional[str] = None,
    target: Optional[str] = None,
    equipment: Optional[str] = None,
    search: Optional[str] = None
) -> List[Exercise]:
    """Get exercises with optional filtering."""
    query = select(Exercise)
    
    if body_part:
        query = query.where(Exercise.body_part == body_part)
    if target:
        query = query.where(Exercise.target == target)
    if equipment:
        query = query.where(Exercise.equipment == equipment)
    if search:
        query = query.where(Exercise.name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_exercise_by_id(db: AsyncSession, exercise_id: str) -> Optional[Exercise]:
    """Get single exercise by ID."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar_one_or_none()


async def get_body_parts(db: AsyncSession) -> List[str]:
    """Get all unique body parts."""
    result = await db.execute(select(Exercise.body_part).distinct())
    return [row[0] for row in result.fetchall()]


async def get_targets(db: AsyncSession) -> List[str]:
    """Get all unique target muscles."""
    result = await db.execute(select(Exercise.target).distinct())
    return [row[0] for row in result.fetchall()]


async def get_equipment(db: AsyncSession) -> List[str]:
    """Get all unique equipment types."""
    result = await db.execute(select(Exercise.equipment).distinct())
    return [row[0] for row in result.fetchall()]


# ============== WORKOUT SESSION CRUD ==============

async def create_workout_session(
    db: AsyncSession,
    user_id: int,
    session_data: WorkoutSessionCreate
) -> WorkoutSession:
    """Create a new workout session for a user."""
    session = WorkoutSession(
        user_id=user_id,
        name=session_data.name,
        notes=session_data.notes
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_workout_sessions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20
) -> List[WorkoutSession]:
    """Get all workout sessions for a user."""
    query = (
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id)
        .options(selectinload(WorkoutSession.sets).selectinload(WorkoutSet.exercise))
        .order_by(WorkoutSession.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_workout_session(
    db: AsyncSession,
    session_id: int,
    user_id: int
) -> Optional[WorkoutSession]:
    """Get a specific workout session (must belong to user)."""
    query = (
        select(WorkoutSession)
        .where(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
        .options(selectinload(WorkoutSession.sets).selectinload(WorkoutSet.exercise))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def end_workout_session(
    db: AsyncSession,
    session_id: int,
    user_id: int
) -> Optional[WorkoutSession]:
    """Mark a workout session as ended."""
    session = await get_workout_session(db, session_id, user_id)
    if session:
        session.ended_at = datetime.utcnow()
        await db.commit()
        await db.refresh(session)
    return session


async def delete_workout_session(
    db: AsyncSession,
    session_id: int,
    user_id: int
) -> bool:
    """Delete a workout session."""
    session = await get_workout_session(db, session_id, user_id)
    if session:
        await db.delete(session)
        await db.commit()
        return True
    return False


# ============== WORKOUT SET CRUD ==============

async def add_set_to_session(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    set_data: WorkoutSetCreate
) -> Optional[WorkoutSet]:
    """Add a set to a workout session (validates ownership)."""
    # Verify session belongs to user
    session = await get_workout_session(db, session_id, user_id)
    if not session:
        return None
    
    workout_set = WorkoutSet(
        session_id=session_id,
        exercise_id=set_data.exercise_id,
        set_number=set_data.set_number,
        reps=set_data.reps,
        weight=set_data.weight,
        duration_seconds=set_data.duration_seconds,
        notes=set_data.notes
    )
    db.add(workout_set)
    await db.commit()
    await db.refresh(workout_set)
    
    # Load exercise relationship
    result = await db.execute(
        select(WorkoutSet)
        .where(WorkoutSet.id == workout_set.id)
        .options(selectinload(WorkoutSet.exercise))
    )
    return result.scalar_one()


async def delete_workout_set(
    db: AsyncSession,
    set_id: int,
    user_id: int
) -> bool:
    """Delete a workout set (validates ownership via session)."""
    query = (
        select(WorkoutSet)
        .join(WorkoutSession)
        .where(WorkoutSet.id == set_id, WorkoutSession.user_id == user_id)
    )
    result = await db.execute(query)
    workout_set = result.scalar_one_or_none()
    
    if workout_set:
        await db.delete(workout_set)
        await db.commit()
        return True
    return False
