# app/models.py
import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey,
    DateTime, Enum, Text, func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ─── Enums for structured feedback ───────────────────
class SorenessLevel(str, enum.Enum):
    none = "none"
    light = "light"
    moderate = "moderate"
    severe = "severe"

class PumpLevel(str, enum.Enum):
    none = "none"
    light = "light"
    moderate = "moderate"
    great = "great"

class VolumeFeeling(str, enum.Enum):
    too_little = "too_little"
    just_right = "just_right"
    too_much = "too_much"

# ─── User ────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    mesocycles = relationship("Mesocycle", back_populates="user", cascade="all, delete-orphan")

# ─── Exercise (from CSV import) ─────────────────────
class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    body_part = Column(String, nullable=False, index=True)
    equipment = Column(String, nullable=True)
    target = Column(String, nullable=False, index=True)

# ═══════════════════════════════════════════════════════
# STATIC LAYER — Plan Templates
# ═══════════════════════════════════════════════════════
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="plans")
    days = relationship("PlanDay", back_populates="plan", cascade="all, delete-orphan",
                        order_by="PlanDay.order")

class PlanDay(Base):
    __tablename__ = "plan_days"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)

    plan = relationship("Plan", back_populates="days")
    exercises = relationship("PlanDayExercise", back_populates="plan_day",
                             cascade="all, delete-orphan", order_by="PlanDayExercise.order")

class PlanDayExercise(Base):
    __tablename__ = "plan_day_exercises"

    id = Column(Integer, primary_key=True, index=True)
    plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    order = Column(Integer, nullable=False)

    plan_day = relationship("PlanDay", back_populates="exercises")
    exercise = relationship("Exercise")

# ═══════════════════════════════════════════════════════
# EXECUTION LAYER — Mesocycle
# ═══════════════════════════════════════════════════════
class Mesocycle(Base):
    __tablename__ = "mesocycles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    name = Column(String, nullable=False)
    current_week = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="mesocycles")
    plan = relationship("Plan")
    weeks = relationship("MesocycleWeek", back_populates="mesocycle",
                         cascade="all, delete-orphan", order_by="MesocycleWeek.week_number")

class MesocycleWeek(Base):
    __tablename__ = "mesocycle_weeks"

    id = Column(Integer, primary_key=True, index=True)
    mesocycle_id = Column(Integer, ForeignKey("mesocycles.id"), nullable=False)
    week_number = Column(Integer, nullable=False)

    mesocycle = relationship("Mesocycle", back_populates="weeks")
    days = relationship("MesocycleDay", back_populates="week",
                        cascade="all, delete-orphan", order_by="MesocycleDay.day_order")

class MesocycleDay(Base):
    __tablename__ = "mesocycle_days"

    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, ForeignKey("mesocycle_weeks.id"), nullable=False)
    plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=False)
    day_order = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)

    week = relationship("MesocycleWeek", back_populates="days")
    plan_day = relationship("PlanDay")
    exercises = relationship("MesocycleDayExercise", back_populates="meso_day",
                             cascade="all, delete-orphan", order_by="MesocycleDayExercise.exercise_order")
    feedbacks = relationship("Feedback", back_populates="meso_day", cascade="all, delete-orphan")

class MesocycleDayExercise(Base):
    __tablename__ = "mesocycle_day_exercises"

    id = Column(Integer, primary_key=True, index=True)
    meso_day_id = Column(Integer, ForeignKey("mesocycle_days.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    exercise_order = Column(Integer, nullable=False)
    prescribed_sets = Column(Integer, nullable=False, default=2)
    prescribed_reps = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)

    meso_day = relationship("MesocycleDay", back_populates="exercises")
    exercise = relationship("Exercise")
    set_logs = relationship("SetLog", back_populates="meso_day_exercise",
                            cascade="all, delete-orphan", order_by="SetLog.set_number")

# ═══════════════════════════════════════════════════════
# MEASUREMENT LAYER — SetLog & Feedback
# ═══════════════════════════════════════════════════════
class SetLog(Base):
    __tablename__ = "set_logs"

    id = Column(Integer, primary_key=True, index=True)
    meso_day_exercise_id = Column(Integer, ForeignKey("mesocycle_day_exercises.id"), nullable=False)
    set_number = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    meso_day_exercise = relationship("MesocycleDayExercise", back_populates="set_logs")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    meso_day_id = Column(Integer, ForeignKey("mesocycle_days.id"), nullable=False)
    muscle_group = Column(String, nullable=False)
    soreness = Column(Enum(SorenessLevel), nullable=False, default=SorenessLevel.none)
    pump = Column(Enum(PumpLevel), nullable=False, default=PumpLevel.none)
    volume_feeling = Column(Enum(VolumeFeeling), nullable=False, default=VolumeFeeling.just_right)
    notes = Column(Text, nullable=True)

    meso_day = relationship("MesocycleDay", back_populates="feedbacks")
