# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

# ─── Auth ─────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

# ─── User ─────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

# ─── Exercise ─────────────────────────────────────────
class ExerciseResponse(BaseModel):
    id: int
    name: str
    body_part: str
    equipment: Optional[str] = None
    target: str

    class Config:
        from_attributes = True

# ═══════════════════════════════════════════════════════
# PLAN
# ═══════════════════════════════════════════════════════
class PlanDayExerciseCreate(BaseModel):
    exercise_id: int
    order: int

class PlanDayCreate(BaseModel):
    name: str
    order: int
    exercises: List[PlanDayExerciseCreate] = []

class PlanCreate(BaseModel):
    name: str
    days: List[PlanDayCreate] = []

class PlanDayExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    order: int
    exercise: ExerciseResponse

    class Config:
        from_attributes = True

class PlanDayResponse(BaseModel):
    id: int
    name: str
    order: int
    exercises: List[PlanDayExerciseResponse] = []

    class Config:
        from_attributes = True

class PlanResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    days: List[PlanDayResponse] = []

    class Config:
        from_attributes = True

# ═══════════════════════════════════════════════════════
# MESOCYCLE
# ═══════════════════════════════════════════════════════
class MesocycleCreate(BaseModel):
    plan_id: int
    name: str

# -- SetLog --
class SetLogCreate(BaseModel):
    set_number: int
    weight: float
    reps: int

class SetLogResponse(BaseModel):
    id: int
    set_number: int
    weight: float
    reps: int
    logged_at: datetime

    class Config:
        from_attributes = True

# -- Skip Sets --
class SkipSetsRequest(BaseModel):
    from_set: int
    to_set: int

# -- Add Note --
class ExerciseNoteRequest(BaseModel):
    note: str

# -- MesocycleDayExercise --
class MesocycleDayExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_order: int
    prescribed_sets: int
    prescribed_reps: Optional[int] = None
    note: Optional[str] = None
    exercise: ExerciseResponse
    set_logs: List[SetLogResponse] = []

    class Config:
        from_attributes = True

# -- Feedback --
class SorenessLevelEnum(str, Enum):
    none = "none"
    light = "light"
    moderate = "moderate"
    severe = "severe"

class PumpLevelEnum(str, Enum):
    none = "none"
    light = "light"
    moderate = "moderate"
    great = "great"

class VolumeFeelingEnum(str, Enum):
    too_little = "too_little"
    just_right = "just_right"
    too_much = "too_much"

class FeedbackCreate(BaseModel):
    muscle_group: str
    soreness: SorenessLevelEnum = SorenessLevelEnum.none
    pump: PumpLevelEnum = PumpLevelEnum.none
    volume_feeling: VolumeFeelingEnum = VolumeFeelingEnum.just_right
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    muscle_group: str
    soreness: SorenessLevelEnum
    pump: PumpLevelEnum
    volume_feeling: VolumeFeelingEnum
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# -- MesocycleDay --
class MesocycleDayResponse(BaseModel):
    id: int
    plan_day_id: int
    day_order: int
    is_completed: bool
    exercises: List[MesocycleDayExerciseResponse] = []
    feedbacks: List[FeedbackResponse] = []

    class Config:
        from_attributes = True

# -- MesocycleWeek --
class MesocycleWeekResponse(BaseModel):
    id: int
    week_number: int
    days: List[MesocycleDayResponse] = []

    class Config:
        from_attributes = True

# -- Mesocycle (list view) --
class MesocycleResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    current_week: int
    is_active: bool
    started_at: datetime

    class Config:
        from_attributes = True

# -- Mesocycle (detail view) --
class MesocycleDayDetailResponse(BaseModel):
    id: int
    plan_day_id: int
    day_order: int
    is_completed: bool
    day_name: Optional[str] = None
    exercises: List[MesocycleDayExerciseResponse] = []
    feedbacks: List[FeedbackResponse] = []

    class Config:
        from_attributes = True

class MesocycleWeekDetailResponse(BaseModel):
    id: int
    week_number: int
    days: List[MesocycleDayDetailResponse] = []

    class Config:
        from_attributes = True

class MesocycleDetailResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    current_week: int
    is_active: bool
    started_at: datetime
    weeks: List[MesocycleWeekDetailResponse] = []

    class Config:
        from_attributes = True

# ═══════════════════════════════════════════════════════
# PROGRESSION (Per-Exercise, Per-Day — existing)
# ═══════════════════════════════════════════════════════
class ProgressionRecommendation(BaseModel):
    exercise_id: int
    exercise_name: str
    current_sets: int
    recommended_sets: int
    reason: str

# ═══════════════════════════════════════════════════════
# FEEDBACK-DRIVEN PROGRESSION (Per-Muscle, Per-Week — new)
# ═══════════════════════════════════════════════════════
class ProgressionDecision(BaseModel):
    muscle_group: str
    current_sets: int
    recommended_sets: int
    delta: int
    reason: str
    confidence: str

    class Config:
        from_attributes = True

class WeekProgressionPlan(BaseModel):
    mesocycle_id: int
    from_week: int
    to_week: int
    decisions: List[ProgressionDecision]
    auto_applied: bool = False

    class Config:
        from_attributes = True

# ═══════════════════════════════════════════════════════
# EXERCISE HISTORY
# ═══════════════════════════════════════════════════════
class SetHistoryItem(BaseModel):
    set_number: int
    weight: float
    reps: int

class ExerciseHistoryItem(BaseModel):
    mesocycle_name: str
    week_number: int
    prescribed_sets: int
    sets: List[SetHistoryItem] = []

class AutofillResponse(BaseModel):
    weight: float
    reps: int

# ═══════════════════════════════════════════════════════
# SMART PROGRESSION — Target Recommendations
# ═══════════════════════════════════════════════════════

class ProgressionType(str, Enum):
    add_set = "add_set"
    add_reps = "add_reps"
    add_weight = "add_weight"
    maintain = "maintain"
    deload = "deload"

class SetTarget(BaseModel):
    set_number: int
    target_weight: float
    target_reps: int
    is_new_set: bool = False  # True if this set was added by progression

class ExerciseProgressionTarget(BaseModel):
    mde_id: int
    exercise_id: int
    exercise_name: str
    muscle_group: str
    progression_type: ProgressionType
    reason: str
    prescribed_sets: int  # total sets including any new ones
    set_targets: List[SetTarget] = []

class DayProgressionTargets(BaseModel):
    meso_day_id: int
    targets: List[ExerciseProgressionTarget] = []

class SetPerformanceVerdict(str, Enum):
    hit = "hit"           # matched target
    improved = "improved"  # beat target
    decreased = "decreased"  # below target
