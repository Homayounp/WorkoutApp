# app/crud.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List, Dict
from app import models
from app.utils import hash_password


# ═══════════════════════════════════════════════════════════════════════════
# PROGRESSION ENGINE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Weight progression
WEEKLY_WEIGHT_INCREMENT_PCT = 0.025   # 2.5% target weekly increase
MIN_BARBELL_INCREMENT_KG = 2.5        # Smallest barbell plate jump
MIN_DUMBBELL_INCREMENT_KG = 2.0       # Smallest dumbbell jump

# Standard dumbbell weights available in most gyms (in kg)
DUMBBELL_WEIGHTS_KG = [
    2, 4, 5, 6, 7.5, 8, 10, 12, 12.5, 14, 15, 16, 17.5, 20,
    22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50,
    52.5, 55, 57.5, 60
]

# Rep ranges for hypertrophy
DEFAULT_REP_FLOOR = 8
DEFAULT_REP_CEILING = 12
ABSOLUTE_REP_CAP = 20  # Never prescribe more than this

# Volume limits
MIN_SETS_PER_EXERCISE = 2
MAX_SETS_PER_EXERCISE = 6

# Feedback thresholds
SORENESS_OVERTRAINED_THRESHOLD = 2.5
SORENESS_UNDER_RECOVERED_THRESHOLD = 1.5
SORENESS_FULLY_RECOVERED_THRESHOLD = 0.5

DELOAD_WEIGHT_REDUCTION = 0.10  # 10% weight reduction on deload


# ═══════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, name: str, email: str, password: str):
    hashed = hash_password(password)
    db_user = models.User(name=name, email=email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ═══════════════════════════════════════════════════════
# EXERCISES (read-only after CSV import)
# ═══════════════════════════════════════════════════════

def get_exercises(db: Session, skip: int = 0, limit: int = 50,
                  body_part: str | None = None, target: str | None = None,
                  search: str | None = None):
    q = db.query(models.Exercise)
    if body_part:
        q = q.filter(models.Exercise.body_part.ilike(body_part))
    if target:
        q = q.filter(models.Exercise.target.ilike(target))
    if search:
        q = q.filter(models.Exercise.name.ilike(f"%{search}%"))
    return q.order_by(models.Exercise.name).offset(skip).limit(limit).all()


def get_exercise_by_id(db: Session, exercise_id: int):
    return db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()


# ═══════════════════════════════════════════════════════
# PLANS (Static Template)
# ═══════════════════════════════════════════════════════

def create_plan(db: Session, user_id: int, name: str, days_data: list):
    plan = models.Plan(user_id=user_id, name=name)
    db.add(plan)
    db.flush()

    for d in days_data:
        day = models.PlanDay(plan_id=plan.id, name=d["name"], order=d["order"])
        db.add(day)
        db.flush()
        for ex in d.get("exercises", []):
            pde = models.PlanDayExercise(
                plan_day_id=day.id,
                exercise_id=ex["exercise_id"],
                order=ex["order"],
            )
            db.add(pde)

    db.commit()
    db.refresh(plan)
    return plan


def get_plans(db: Session, user_id: int):
    return (
        db.query(models.Plan)
        .filter(models.Plan.user_id == user_id)
        .options(
            joinedload(models.Plan.days)
            .joinedload(models.PlanDay.exercises)
            .joinedload(models.PlanDayExercise.exercise)
        )
        .all()
    )


def get_plan_by_id(db: Session, plan_id: int, user_id: int):
    return (
        db.query(models.Plan)
        .filter(models.Plan.id == plan_id, models.Plan.user_id == user_id)
        .options(
            joinedload(models.Plan.days)
            .joinedload(models.PlanDay.exercises)
            .joinedload(models.PlanDayExercise.exercise)
        )
        .first()
    )


def delete_plan(db: Session, plan_id: int, user_id: int):
    plan = db.query(models.Plan).filter(
        models.Plan.id == plan_id, models.Plan.user_id == user_id
    ).first()
    if not plan:
        return False
    # Check if any mesocycle uses this plan
    meso_count = db.query(models.Mesocycle).filter(
        models.Mesocycle.plan_id == plan_id
    ).count()
    if meso_count > 0:
        return "in_use"
    db.delete(plan)
    db.commit()
    return True


# ═══════════════════════════════════════════════════════
# MESOCYCLE (Execution Layer)
# ═══════════════════════════════════════════════════════

def start_mesocycle(db: Session, user_id: int, plan_id: int, name: str):
    plan = get_plan_by_id(db, plan_id, user_id)
    if not plan:
        return None

    meso = models.Mesocycle(user_id=user_id, plan_id=plan_id, name=name)
    db.add(meso)
    db.flush()

    week = models.MesocycleWeek(mesocycle_id=meso.id, week_number=1)
    db.add(week)
    db.flush()

    for plan_day in plan.days:
        md = models.MesocycleDay(
            week_id=week.id,
            plan_day_id=plan_day.id,
            day_order=plan_day.order,
        )
        db.add(md)
        db.flush()

        for pde in plan_day.exercises:
            mde = models.MesocycleDayExercise(
                meso_day_id=md.id,
                exercise_id=pde.exercise_id,
                exercise_order=pde.order,
                prescribed_sets=2,
            )
            db.add(mde)

    db.commit()
    db.refresh(meso)
    return meso


def get_mesocycles(db: Session, user_id: int):
    return (
        db.query(models.Mesocycle)
        .filter(models.Mesocycle.user_id == user_id)
        .order_by(models.Mesocycle.started_at.desc())
        .all()
    )


def get_mesocycle_detail(db: Session, mesocycle_id: int, user_id: int):
    return (
        db.query(models.Mesocycle)
        .filter(models.Mesocycle.id == mesocycle_id, models.Mesocycle.user_id == user_id)
        .options(
            joinedload(models.Mesocycle.weeks)
            .joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
            joinedload(models.Mesocycle.weeks)
            .joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.set_logs),
            joinedload(models.Mesocycle.weeks)
            .joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.feedbacks),
            joinedload(models.Mesocycle.weeks)
            .joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.plan_day),
        )
        .first()
    )


def delete_mesocycle(db: Session, mesocycle_id: int, user_id: int):
    meso = db.query(models.Mesocycle).filter(
        models.Mesocycle.id == mesocycle_id,
        models.Mesocycle.user_id == user_id,
    ).first()
    if not meso:
        return False
    db.delete(meso)
    db.commit()
    return True


def get_current_workout(db: Session, mesocycle_id: int, user_id: int):
    meso = (
        db.query(models.Mesocycle)
        .filter(models.Mesocycle.id == mesocycle_id, models.Mesocycle.user_id == user_id)
        .first()
    )
    if not meso:
        return None

    week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == meso.id,
            models.MesocycleWeek.week_number == meso.current_week,
        )
        .first()
    )
    if not week:
        return None

    day = (
        db.query(models.MesocycleDay)
        .filter(
            models.MesocycleDay.week_id == week.id,
            models.MesocycleDay.is_completed == False,
        )
        .options(
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.set_logs),
            joinedload(models.MesocycleDay.feedbacks),
            joinedload(models.MesocycleDay.plan_day),
        )
        .order_by(models.MesocycleDay.day_order)
        .first()
    )
    return day


# ═══════════════════════════════════════════════════════
# SET LOGGING
# ═══════════════════════════════════════════════════════

def log_set(db: Session, meso_day_exercise_id: int, set_number: int,
            weight: float, reps: int):
    # Check if set already exists (update instead of duplicate)
    existing = db.query(models.SetLog).filter(
        models.SetLog.meso_day_exercise_id == meso_day_exercise_id,
        models.SetLog.set_number == set_number,
    ).first()
    if existing:
        existing.weight = weight
        existing.reps = reps
        db.commit()
        db.refresh(existing)
        return existing

    sl = models.SetLog(
        meso_day_exercise_id=meso_day_exercise_id,
        set_number=set_number,
        weight=weight,
        reps=reps,
    )
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl


def skip_sets(db: Session, meso_day_exercise_id: int, from_set: int, to_set: int):
    """Mark sets as skipped by logging them with weight=0, reps=0."""
    results = []
    for s in range(from_set, to_set + 1):
        existing = db.query(models.SetLog).filter(
            models.SetLog.meso_day_exercise_id == meso_day_exercise_id,
            models.SetLog.set_number == s,
        ).first()
        if existing:
            existing.weight = 0
            existing.reps = 0
        else:
            existing = models.SetLog(
                meso_day_exercise_id=meso_day_exercise_id,
                set_number=s, weight=0, reps=0,
            )
            db.add(existing)
        results.append(existing)
    db.commit()
    return results


def add_set_to_exercise(db: Session, meso_day_exercise_id: int):
    """Increase prescribed_sets by 1."""
    mde = db.query(models.MesocycleDayExercise).filter(
        models.MesocycleDayExercise.id == meso_day_exercise_id
    ).first()
    if not mde:
        return None
    mde.prescribed_sets += 1
    db.commit()
    db.refresh(mde)
    return mde


# ═══════════════════════════════════════════════════════
# EXERCISE NOTES
# ═══════════════════════════════════════════════════════

def save_exercise_note(db: Session, meso_day_exercise_id: int, note: str):
    mde = db.query(models.MesocycleDayExercise).filter(
        models.MesocycleDayExercise.id == meso_day_exercise_id
    ).first()
    if not mde:
        return None
    mde.note = note
    db.commit()
    db.refresh(mde)
    return mde


# ═══════════════════════════════════════════════════════
# EXERCISE HISTORY
# ═══════════════════════════════════════════════════════

def get_exercise_history(db: Session, exercise_id: int, user_id: int, limit: int = 10):
    rows = (
        db.query(models.MesocycleDayExercise)
        .join(models.MesocycleDay)
        .join(models.MesocycleWeek)
        .join(models.Mesocycle)
        .filter(
            models.Mesocycle.user_id == user_id,
            models.MesocycleDayExercise.exercise_id == exercise_id,
            models.MesocycleDay.is_completed == True,
        )
        .options(
            joinedload(models.MesocycleDayExercise.set_logs),
            joinedload(models.MesocycleDayExercise.meso_day)
            .joinedload(models.MesocycleDay.week)
            .joinedload(models.MesocycleWeek.mesocycle),
        )
        .order_by(models.MesocycleDayExercise.id.desc())
        .limit(limit)
        .all()
    )

    history = []
    for mde in rows:
        sets_data = []
        for sl in sorted(mde.set_logs, key=lambda x: x.set_number):
            sets_data.append({
                "set_number": sl.set_number,
                "weight": sl.weight,
                "reps": sl.reps,
            })
        week_num = mde.meso_day.week.week_number if mde.meso_day.week else 0
        meso_name = mde.meso_day.week.mesocycle.name if mde.meso_day.week else ""
        history.append({
            "mesocycle_name": meso_name,
            "week_number": week_num,
            "prescribed_sets": mde.prescribed_sets,
            "sets": sets_data,
        })

    return history


# ═══════════════════════════════════════════════════════
# AUTOFILL
# ═══════════════════════════════════════════════════════

def get_last_weight_for_exercise(db: Session, exercise_id: int, user_id: int):
    row = (
        db.query(models.SetLog)
        .join(models.MesocycleDayExercise)
        .join(models.MesocycleDay)
        .join(models.MesocycleWeek)
        .join(models.Mesocycle)
        .filter(
            models.Mesocycle.user_id == user_id,
            models.MesocycleDayExercise.exercise_id == exercise_id,
            models.SetLog.weight > 0,
        )
        .order_by(models.SetLog.logged_at.desc())
        .first()
    )
    if row:
        return {"weight": row.weight, "reps": row.reps}
    return None


# ═══════════════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════════════

def create_feedback(db: Session, meso_day_id: int, muscle_group: str,
                    soreness: str, pump: str, volume_feeling: str,
                    notes: str | None = None):
    existing = db.query(models.Feedback).filter(
        models.Feedback.meso_day_id == meso_day_id,
        models.Feedback.muscle_group == muscle_group,
    ).first()
    if existing:
        existing.soreness = soreness
        existing.pump = pump
        existing.volume_feeling = volume_feeling
        existing.notes = notes
        db.commit()
        db.refresh(existing)
        return existing

    fb = models.Feedback(
        meso_day_id=meso_day_id,
        muscle_group=muscle_group,
        soreness=soreness,
        pump=pump,
        volume_feeling=volume_feeling,
        notes=notes,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


# ═══════════════════════════════════════════════════════
# COMPLETE DAY & PER-DAY PROGRESSION (existing)
# ═══════════════════════════════════════════════════════

def complete_day(db: Session, meso_day_id: int):
    day = db.query(models.MesocycleDay).filter(models.MesocycleDay.id == meso_day_id).first()
    if day:
        day.is_completed = True
        db.commit()
    return day


def calculate_progression(db: Session, meso_day_id: int):
    day = (
        db.query(models.MesocycleDay)
        .filter(models.MesocycleDay.id == meso_day_id)
        .options(
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
            joinedload(models.MesocycleDay.feedbacks),
        )
        .first()
    )
    if not day:
        return []

    fb_map: dict[str, models.Feedback] = {}
    for fb in day.feedbacks:
        fb_map[fb.muscle_group.lower()] = fb

    recommendations = []
    for mde in day.exercises:
        target = mde.exercise.target.lower()
        fb = fb_map.get(target)

        current = mde.prescribed_sets
        recommended = current
        reason = "No change — maintain current volume."

        if fb:
            if fb.volume_feeling == models.VolumeFeeling.too_little:
                recommended = current + 1
                reason = "Volume felt too little → +1 set."
            elif fb.volume_feeling == models.VolumeFeeling.too_much:
                recommended = max(1, current - 1)
                reason = "Volume felt too much → -1 set."
            elif fb.soreness == models.SorenessLevel.severe:
                recommended = max(1, current - 1)
                reason = "Severe soreness → -1 set for recovery."
            elif (fb.pump == models.PumpLevel.great
                  and fb.volume_feeling == models.VolumeFeeling.just_right):
                recommended = current + 1
                reason = "Great pump + volume just right → +1 set (progressive overload)."

        recommendations.append({
            "exercise_id": mde.exercise_id,
            "exercise_name": mde.exercise.name,
            "current_sets": current,
            "recommended_sets": recommended,
            "reason": reason,
        })

    return recommendations


def apply_progression_to_next_week(db: Session, mesocycle_id: int, user_id: int):
    meso = (
        db.query(models.Mesocycle)
        .filter(models.Mesocycle.id == mesocycle_id, models.Mesocycle.user_id == user_id)
        .first()
    )
    if not meso:
        return None

    current_week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == meso.id,
            models.MesocycleWeek.week_number == meso.current_week,
        )
        .first()
    )
    if not current_week:
        return None

    days = (
        db.query(models.MesocycleDay)
        .filter(models.MesocycleDay.week_id == current_week.id)
        .options(
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
            joinedload(models.MesocycleDay.feedbacks),
        )
        .order_by(models.MesocycleDay.day_order)
        .all()
    )

    if not all(d.is_completed for d in days):
        return None

    new_week_number = meso.current_week + 1
    new_week = models.MesocycleWeek(mesocycle_id=meso.id, week_number=new_week_number)
    db.add(new_week)
    db.flush()

    for old_day in days:
        recs = calculate_progression(db, old_day.id)
        rec_map = {r["exercise_id"]: r["recommended_sets"] for r in recs}

        new_day = models.MesocycleDay(
            week_id=new_week.id,
            plan_day_id=old_day.plan_day_id,
            day_order=old_day.day_order,
        )
        db.add(new_day)
        db.flush()

        for old_mde in old_day.exercises:
            new_sets = rec_map.get(old_mde.exercise_id, old_mde.prescribed_sets)
            new_mde = models.MesocycleDayExercise(
                meso_day_id=new_day.id,
                exercise_id=old_mde.exercise_id,
                exercise_order=old_mde.exercise_order,
                prescribed_sets=new_sets,
            )
            db.add(new_mde)

    meso.current_week = new_week_number
    db.commit()
    db.refresh(meso)
    return meso


# ═══════════════════════════════════════════════════════
# FEEDBACK-DRIVEN PROGRESSION (Week-Level Intelligence)
# ═══════════════════════════════════════════════════════

def calculate_feedback_driven_progression(db: Session, mesocycle_id: int, user_id: int):
    """
    Analyze ALL feedback from the current week across ALL days,
    aggregate per muscle group, and return intelligent set-volume
    recommendations for the next week.

    This is the WEEK-LEVEL algorithm (vs calculate_progression which is per-day).
    Uses a multi-signal decision matrix: soreness × pump × volume_feeling.
    """
    meso = db.query(models.Mesocycle).filter(
        models.Mesocycle.id == mesocycle_id,
        models.Mesocycle.user_id == user_id,
    ).first()

    if not meso:
        return []

    # ── Find the current week with all data loaded ────
    current_week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == meso.id,
            models.MesocycleWeek.week_number == meso.current_week,
        )
        .options(
            joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.feedbacks),
            joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
        )
        .first()
    )

    if not current_week:
        return []

    # ── Aggregate feedback per muscle group across ALL days ──
    muscle_feedbacks: dict[str, list] = {}
    muscle_current_sets: dict[str, int] = {}
    muscle_exercise_count: dict[str, int] = {}

    for day in current_week.days:
        for fb in day.feedbacks:
            group = fb.muscle_group
            if group not in muscle_feedbacks:
                muscle_feedbacks[group] = []
            muscle_feedbacks[group].append(fb)

        for mde in day.exercises:
            group = mde.exercise.body_part
            if group not in muscle_current_sets:
                muscle_current_sets[group] = 0
                muscle_exercise_count[group] = 0
            muscle_current_sets[group] += mde.prescribed_sets
            muscle_exercise_count[group] += 1

    if not muscle_feedbacks:
        return []

    # ── Scoring maps ─────────────────────────────────
    soreness_scores = {"none": 0, "light": 1, "moderate": 2, "severe": 3}
    pump_scores = {"none": 0, "light": 1, "moderate": 2, "great": 3}
    volume_scores = {"too_little": -1, "just_right": 0, "too_much": 1}

    def _enum_val(field):
        """Safely extract string value from enum or string."""
        return field.value if hasattr(field, 'value') else str(field)

    # ── Apply decision matrix per muscle group ────────
    decisions = []

    for muscle_group, feedbacks in muscle_feedbacks.items():
        n = len(feedbacks)

        avg_soreness = sum(
            soreness_scores.get(_enum_val(fb.soreness), 0) for fb in feedbacks
        ) / n

        avg_pump = sum(
            pump_scores.get(_enum_val(fb.pump), 0) for fb in feedbacks
        ) / n

        avg_volume = sum(
            volume_scores.get(_enum_val(fb.volume_feeling), 0) for fb in feedbacks
        ) / n

        current_sets = muscle_current_sets.get(muscle_group, 0)
        min_sets = muscle_exercise_count.get(muscle_group, 1)

        # ── Multi-signal decision matrix ──────────────
        delta = 0
        reason = ""
        confidence = "medium"

        # Priority 1: Severe soreness overrides everything
        if avg_soreness >= 2.5:
            delta = -2
            reason = (
                f"Severe soreness detected (avg {avg_soreness:.1f}/3). "
                f"Significant volume reduction to allow recovery."
            )
            confidence = "high"

        # Priority 2: Volume felt too little
        elif avg_volume <= -0.5:
            if avg_soreness <= 1.0:
                delta = 1
                reason = (
                    f"Volume felt insufficient (avg {avg_volume:.1f}) with low soreness "
                    f"({avg_soreness:.1f}/3). Safe to add volume."
                )
                confidence = "high"
            else:
                delta = 0
                reason = (
                    f"Volume felt low ({avg_volume:.1f}) but soreness is elevated "
                    f"({avg_soreness:.1f}/3). Holding steady — recovery takes priority."
                )
                confidence = "medium"

        # Priority 3: Volume felt too much
        elif avg_volume >= 0.5:
            if avg_soreness >= 1.5:
                delta = -2
                reason = (
                    f"Excessive volume ({avg_volume:.1f}) combined with significant "
                    f"soreness ({avg_soreness:.1f}/3). Dropping 2 sets."
                )
                confidence = "high"
            else:
                delta = -1
                reason = (
                    f"Volume felt excessive ({avg_volume:.1f}). "
                    f"Reducing by 1 set to find optimal stimulus."
                )
                confidence = "high"

        # Priority 4: Volume just right — fine-tune based on other signals
        else:
            if avg_soreness >= 2.0:
                delta = -1
                reason = (
                    f"Volume feels right but recovery is lagging "
                    f"(soreness {avg_soreness:.1f}/3). Slight reduction."
                )
                confidence = "medium"
            elif avg_pump >= 2.0 and avg_soreness <= 1.0:
                delta = 1
                reason = (
                    f"Optimal signals: great pump ({avg_pump:.1f}/3), low soreness "
                    f"({avg_soreness:.1f}/3), volume on point. Adding for progressive overload."
                )
                confidence = "high"
            elif avg_pump < 1.0 and avg_soreness <= 1.0:
                delta = 0
                reason = (
                    f"Volume feels right but pump is weak ({avg_pump:.1f}/3). "
                    f"Consider improving mind-muscle connection or exercise selection. "
                    f"Holding volume."
                )
                confidence = "low"
            else:
                delta = 0
                reason = "All signals nominal. Maintaining current volume."
                confidence = "medium"

        # ── Enforce minimums ─────────────────────────
        recommended = max(current_sets + delta, min_sets)
        actual_delta = recommended - current_sets

        decisions.append({
            "muscle_group": muscle_group,
            "current_sets": current_sets,
            "recommended_sets": recommended,
            "delta": actual_delta,
            "reason": reason,
            "confidence": confidence,
        })

    return decisions


def apply_feedback_progression(db: Session, mesocycle_id: int, user_id: int, decisions: list):
    """
    Apply feedback-driven progression decisions to the NEXT week's exercises.
    Distributes set changes evenly across exercises targeting each muscle group.
    Returns number of adjustments made, or None if next week doesn't exist.
    """
    meso = db.query(models.Mesocycle).filter(
        models.Mesocycle.id == mesocycle_id,
        models.Mesocycle.user_id == user_id,
    ).first()

    if not meso:
        return None

    next_week_num = meso.current_week + 1

    next_week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == meso.id,
            models.MesocycleWeek.week_number == next_week_num,
        )
        .options(
            joinedload(models.MesocycleWeek.days)
            .joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
        )
        .first()
    )

    if not next_week:
        return None

    # Build a map: muscle_group → delta
    delta_map = {}
    for d in decisions:
        delta_map[d["muscle_group"]] = d["delta"]

    adjustments = 0
    for day in next_week.days:
        for mde in day.exercises:
            group = mde.exercise.body_part
            delta = delta_map.get(group, 0)
            if delta != 0:
                # Distribute delta across exercises for this muscle group
                # For simplicity, apply delta to each exercise (clamped)
                new_sets = max(MIN_SETS_PER_EXERCISE, min(MAX_SETS_PER_EXERCISE,
                               mde.prescribed_sets + delta))
                if new_sets != mde.prescribed_sets:
                    mde.prescribed_sets = new_sets
                    adjustments += 1

    db.commit()
    return adjustments


# ═══════════════════════════════════════════════════════════════════════════
# PROGRESSION ENGINE — HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def classify_recovery_state(avg_soreness: float) -> str:
    """
    Classify recovery state based on average soreness score (0-3 scale).

    Returns one of:
        'overtrained'       — soreness >= 2.5 → deload
        'under_recovered'   — soreness >= 1.5 → maintain, no progression
        'mostly_recovered'  — soreness >= 0.5 → normal progression
        'fully_recovered'   — soreness < 0.5  → aggressive progression OK
    """
    if avg_soreness >= SORENESS_OVERTRAINED_THRESHOLD:
        return "overtrained"
    elif avg_soreness >= SORENESS_UNDER_RECOVERED_THRESHOLD:
        return "under_recovered"
    elif avg_soreness >= SORENESS_FULLY_RECOVERED_THRESHOLD:
        return "mostly_recovered"
    else:
        return "fully_recovered"


def classify_stimulus_quality(avg_pump: float, avg_volume_feeling: float) -> str:
    """
    Classify training stimulus quality based on pump and volume perception.

    Args:
        avg_pump: 0-3 scale (none=0, light=1, moderate=2, great=3)
        avg_volume_feeling: -1 to +1 scale (too_little=-1, just_right=0, too_much=+1)

    Returns one of: 'insufficient', 'optimal', 'excessive'
    """
    # Normalize pump to 0-1 range
    pump_normalized = avg_pump / 3.0

    # Normalize volume feeling to 0-1 range
    volume_normalized = (avg_volume_feeling + 1) / 2.0

    # Combined stimulus score: pump dominates, volume feeling modulates
    # Range: 0 (no stimulus at all) → ~1.5 (maximum stimulus)
    stimulus_score = pump_normalized + (volume_normalized * 0.5)

    if stimulus_score < 0.5:
        return "insufficient"
    elif stimulus_score <= 1.0:
        return "optimal"
    else:
        return "excessive"


def is_dumbbell_exercise(exercise_name: str, equipment: str | None = None) -> bool:
    """
    Determine if an exercise uses dumbbells.

    Checks the equipment field first (from Exercise model), then falls back
    to heuristic name matching.

    Args:
        exercise_name: The exercise name string
        equipment: The equipment field from the Exercise model (if available)

    Returns:
        True if the exercise uses dumbbells
    """
    # Check equipment field first (most reliable)
    if equipment:
        eq_lower = equipment.lower()
        if "dumbbell" in eq_lower or "db" in eq_lower:
            return True
        # If equipment explicitly says barbell/machine/cable, it's not dumbbell
        if any(kw in eq_lower for kw in ["barbell", "machine", "cable", "smith",
                                          "body weight", "bodyweight", "band"]):
            return False

    # Fall back to name heuristic
    dumbbell_keywords = [
        'dumbbell', 'db ', 'db_', 'd.b.',
        'lateral raise', 'fly', 'flye',
        'concentration curl', 'hammer curl', 'kickback',
    ]
    name_lower = exercise_name.lower()
    return any(kw in name_lower for kw in dumbbell_keywords)


def get_next_available_weight(
    current_weight: float,
    is_dumbbell: bool,
    target_increment_pct: float = WEEKLY_WEIGHT_INCREMENT_PCT
) -> tuple:
    """
    Calculate the next available weight, respecting equipment constraints.

    For dumbbells: snaps to the next available standard weight.
    For barbells/machines: rounds to the nearest 2.5kg increment.

    Args:
        current_weight: Current working weight in kg
        is_dumbbell: Whether this exercise uses dumbbells
        target_increment_pct: Target percentage increase (default 2.5%)

    Returns:
        (next_weight: float, can_achieve: bool, reason: str)
        - next_weight: the weight to prescribe
        - can_achieve: True if this weight increase is reasonable
        - reason: human-readable explanation
    """
    if current_weight <= 0:
        return (current_weight, False, "No prior weight data")

    target_increment = current_weight * target_increment_pct
    target_weight = current_weight + target_increment

    if is_dumbbell:
        # Find the smallest dumbbell weight >= target_weight
        available_weights = [w for w in DUMBBELL_WEIGHTS_KG if w >= target_weight]

        if not available_weights:
            return (current_weight, False, "At maximum dumbbell weight")

        next_weight = available_weights[0]
        actual_increment = next_weight - current_weight

        # Safety: if the jump is 0 (already at a dumbbell weight above target)
        if actual_increment <= 0:
            # Current weight is already above target, find strictly next
            strictly_above = [w for w in DUMBBELL_WEIGHTS_KG if w > current_weight]
            if strictly_above:
                next_weight = strictly_above[0]
                actual_increment = next_weight - current_weight
            else:
                return (current_weight, False, "At maximum dumbbell weight")

        actual_increment_pct = actual_increment / current_weight

        # If the jump exceeds 2.5× the target percentage, it's too aggressive
        max_acceptable_pct = target_increment_pct * 2.5
        if actual_increment_pct > max_acceptable_pct:
            return (
                current_weight,
                False,
                f"Next dumbbell ({next_weight}kg) requires {actual_increment_pct:.1%} "
                f"increase, exceeds safe threshold of {max_acceptable_pct:.1%}"
            )

        return (
            next_weight,
            True,
            f"Progressing to {next_weight}kg dumbbell "
            f"({actual_increment_pct:.1%} increase)"
        )

    else:
        # Barbell / machine: round to nearest 2.5kg increment
        increments_needed = round(target_increment / MIN_BARBELL_INCREMENT_KG)
        increments_needed = max(1, increments_needed)
        next_weight = current_weight + (increments_needed * MIN_BARBELL_INCREMENT_KG)

        actual_increment_pct = (next_weight - current_weight) / current_weight

        max_acceptable_pct = target_increment_pct * 2.5
        if actual_increment_pct > max_acceptable_pct:
            return (
                current_weight,
                False,
                f"Weight jump of {actual_increment_pct:.1%} exceeds "
                f"safe threshold of {max_acceptable_pct:.1%}"
            )

        return (
            round(next_weight, 1),
            True,
            f"Progressing to {next_weight}kg ({actual_increment_pct:.1%} increase)"
        )


def calculate_set_target(
    last_weight: float,
    last_reps: int,
    is_dumbbell: bool,
    recovery_state: str,
    stimulus_quality: str,
    rep_floor: int = DEFAULT_REP_FLOOR,
    rep_ceiling: int = DEFAULT_REP_CEILING
) -> dict:
    """
    Calculate the target weight and reps for a SINGLE set using double progression.

    Double Progression Logic:
        1. If recovery is bad → deload (reduce weight) or hold
        2. Try to increase weight by ~2.5%
        3. If weight jump is too large for equipment → increase reps instead
        4. If reps are at ceiling → force the weight jump, reset reps to floor

    Args:
        last_weight: Weight used in the last session for this set
        last_reps: Reps completed in the last session for this set
        is_dumbbell: Whether exercise uses dumbbells (affects weight rounding)
        recovery_state: One of 'overtrained', 'under_recovered',
                        'mostly_recovered', 'fully_recovered'
        stimulus_quality: One of 'insufficient', 'optimal', 'excessive'
        rep_floor: Lower bound of target rep range (default 8)
        rep_ceiling: Upper bound of target rep range (default 12)

    Returns:
        {
            "target_weight": float,
            "target_reps": int,
            "action": str,       # one of: deload, maintain, increase_weight,
                                 #         increase_reps, force_weight_increase, initialize
            "reason": str        # human-readable explanation
        }
    """
    # ── Handle missing data ──
    if last_weight <= 0 or last_reps <= 0:
        return {
            "target_weight": last_weight,
            "target_reps": rep_floor,
            "action": "initialize",
            "reason": "No prior data — using defaults"
        }

    # ═══════════════════════════════════════════════════
    # Priority 1: Handle poor recovery → SAFETY FIRST
    # ═══════════════════════════════════════════════════
    if recovery_state == "overtrained":
        deload_weight = round(last_weight * (1 - DELOAD_WEIGHT_REDUCTION), 1)

        # Snap to valid equipment weight
        if is_dumbbell:
            valid_below = [w for w in DUMBBELL_WEIGHTS_KG if w <= deload_weight]
            if valid_below:
                deload_weight = valid_below[-1]  # Largest dumbbell <= deload target
        else:
            # Round down to nearest 2.5kg
            deload_weight = (deload_weight // MIN_BARBELL_INCREMENT_KG) * MIN_BARBELL_INCREMENT_KG
            deload_weight = round(deload_weight, 1)

        return {
            "target_weight": deload_weight,
            "target_reps": rep_floor,
            "action": "deload",
            "reason": (
                f"Overtrained — deloading weight by {DELOAD_WEIGHT_REDUCTION:.0%} "
                f"({last_weight}→{deload_weight}kg) and resetting reps to {rep_floor}"
            )
        }

    if recovery_state == "under_recovered":
        return {
            "target_weight": last_weight,
            "target_reps": last_reps,
            "action": "maintain",
            "reason": (
                "Under-recovered — maintaining current prescription "
                f"({last_weight}kg × {last_reps}) to allow adaptation"
            )
        }

    # ═══════════════════════════════════════════════════
    # Priority 2: Try weight increase (~2.5% weekly)
    # ═══════════════════════════════════════════════════
    next_weight, can_achieve, weight_reason = get_next_available_weight(
        last_weight, is_dumbbell
    )

    if can_achieve:
        # Weight increase is achievable — apply it
        # When weight goes up, allow reps to drop by 1 to accommodate
        new_reps = last_reps
        if last_reps > rep_floor + 1:
            new_reps = max(rep_floor, last_reps - 1)

        return {
            "target_weight": next_weight,
            "target_reps": new_reps,
            "action": "increase_weight",
            "reason": (
                f"{weight_reason}. "
                f"Reps adjusted to {new_reps} to accommodate heavier load."
            )
        }

    # ═══════════════════════════════════════════════════
    # Priority 3: Can't increase weight → try adding reps
    # ═══════════════════════════════════════════════════
    if last_reps < rep_ceiling:
        new_reps = last_reps + 1
        return {
            "target_weight": last_weight,
            "target_reps": new_reps,
            "action": "increase_reps",
            "reason": (
                f"Weight increment not achievable ({weight_reason}). "
                f"Adding 1 rep ({last_reps}→{new_reps}) at {last_weight}kg instead."
            )
        }

    # ═══════════════════════════════════════════════════
    # Priority 4: Reps at ceiling → FORCE weight jump
    # ═══════════════════════════════════════════════════
    if last_reps >= rep_ceiling:
        if is_dumbbell:
            available_weights = [w for w in DUMBBELL_WEIGHTS_KG if w > last_weight]
            if available_weights:
                forced_weight = available_weights[0]
            else:
                forced_weight = last_weight + MIN_DUMBBELL_INCREMENT_KG
        else:
            forced_weight = last_weight + MIN_BARBELL_INCREMENT_KG

        return {
            "target_weight": round(forced_weight, 1),
            "target_reps": rep_floor,
            "action": "force_weight_increase",
            "reason": (
                f"Reps hit ceiling ({rep_ceiling}). Forcing weight increase to "
                f"{forced_weight}kg and resetting reps to {rep_floor}. "
                f"This is the double progression reset point."
            )
        }

    # ═══════════════════════════════════════════════════
    # Fallback: maintain (should rarely reach here)
    # ═══════════════════════════════════════════════════
    return {
        "target_weight": last_weight,
        "target_reps": last_reps,
        "action": "maintain",
        "reason": "No progression criteria met — maintaining current prescription"
    }


# ═══════════════════════════════════════════════════════════════════════════
# SMART PROGRESSION — THE BRAIN
# ═══════════════════════════════════════════════════════════════════════════

def calculate_smart_progression(
    db: Session,
    meso_day_id: int,
    soreness_overrides: dict | None = None
) -> list:
    """
    Calculate smart progression targets for ALL exercises in a workout day.

    This is the main entry point called by the API. It combines:
    1. Historical performance data (last completed sets)
    2. Biofeedback signals (soreness, pump, volume perception)
    3. Equipment-aware weight rounding (dumbbell vs barbell)
    4. Double progression logic (weight → reps → force weight at ceiling)

    Args:
        db: Database session
        meso_day_id: The MesocycleDay ID to generate targets for
        soreness_overrides: Optional dict of {"muscle_group": "soreness_level"}
                           to override stored feedback (for pre-workout input)

    Returns:
        List of per-exercise target dictionaries:
        [
            {
                "mde_id": int,
                "exercise_id": int,
                "exercise_name": str,
                "muscle_group": str,
                "equipment": str,
                "is_dumbbell": bool,
                "prescribed_sets": int,
                "recovery_state": str,
                "stimulus_quality": str,
                "set_targets": [
                    {
                        "set_number": int,
                        "target_weight": float,
                        "target_reps": int,
                        "action": str,
                        "reason": str,
                        "source": str   # "history" | "autofill" | "no_data"
                    },
                    ...
                ]
            },
            ...
        ]
    """
    # ── Load the workout day with all related data ──
    day = (
        db.query(models.MesocycleDay)
        .filter(models.MesocycleDay.id == meso_day_id)
        .options(
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.exercise),
            joinedload(models.MesocycleDay.exercises)
            .joinedload(models.MesocycleDayExercise.set_logs),
            joinedload(models.MesocycleDay.feedbacks),
            joinedload(models.MesocycleDay.week)
            .joinedload(models.MesocycleWeek.mesocycle),
        )
        .first()
    )

    if not day:
        return []

    # Get user_id through the relationship chain
    user_id = day.week.mesocycle.user_id if day.week and day.week.mesocycle else None

    # ── Build feedback map for this day's muscle groups ──
    # Scoring maps
    soreness_scores = {"none": 0, "light": 1, "moderate": 2, "severe": 3}
    pump_scores = {"none": 0, "light": 1, "moderate": 2, "great": 3}
    volume_scores = {"too_little": -1, "just_right": 0, "too_much": 1}

    def _enum_val(field):
        return field.value if hasattr(field, 'value') else str(field)

    # Aggregate feedback per muscle group from THIS day
    muscle_fb: dict[str, dict] = {}
    for fb in day.feedbacks:
        group = fb.muscle_group.lower()
        soreness_val = soreness_scores.get(_enum_val(fb.soreness), 1)
        pump_val = pump_scores.get(_enum_val(fb.pump), 1.5)
        volume_val = volume_scores.get(_enum_val(fb.volume_feeling), 0)

        if group not in muscle_fb:
            muscle_fb[group] = {"soreness": [], "pump": [], "volume": []}
        muscle_fb[group]["soreness"].append(soreness_val)
        muscle_fb[group]["pump"].append(pump_val)
        muscle_fb[group]["volume"].append(volume_val)

    # Apply soreness overrides if provided (pre-workout user input)
    if soreness_overrides:
        for group, level in soreness_overrides.items():
            group_lower = group.lower()
            override_score = soreness_scores.get(level.lower(), 1)
            if group_lower not in muscle_fb:
                muscle_fb[group_lower] = {"soreness": [], "pump": [], "volume": []}
            # Override replaces all previous soreness readings
            muscle_fb[group_lower]["soreness"] = [override_score]

    # Also check feedback from PREVIOUS days in the same week
    # (important for recovery assessment)
    if day.week:
        for sibling_day in day.week.days:
            if sibling_day.id == day.id:
                continue  # Skip current day
            if not sibling_day.is_completed:
                continue  # Only use completed days

            # Lazy-load feedbacks for sibling days
            sibling_feedbacks = (
                db.query(models.Feedback)
                .filter(models.Feedback.meso_day_id == sibling_day.id)
                .all()
            )
            for fb in sibling_feedbacks:
                group = fb.muscle_group.lower()
                soreness_val = soreness_scores.get(_enum_val(fb.soreness), 1)
                pump_val = pump_scores.get(_enum_val(fb.pump), 1.5)
                volume_val = volume_scores.get(_enum_val(fb.volume_feeling), 0)

                if group not in muscle_fb:
                    muscle_fb[group] = {"soreness": [], "pump": [], "volume": []}
                muscle_fb[group]["soreness"].append(soreness_val)
                muscle_fb[group]["pump"].append(pump_val)
                muscle_fb[group]["volume"].append(volume_val)

    # ── Process each exercise ──
    results = []

    for mde in sorted(day.exercises, key=lambda e: e.exercise_order):
        exercise = mde.exercise
        exercise_name = exercise.name if exercise else "Unknown"
        muscle_group = (exercise.target or exercise.body_part or "unknown").lower()
        equipment = exercise.equipment if exercise else None

        # Determine equipment type
        is_db = is_dumbbell_exercise(exercise_name, equipment)

        # ── Get recovery & stimulus classification for this muscle group ──
        fb_data = muscle_fb.get(muscle_group, None)

        if fb_data and fb_data["soreness"]:
            avg_soreness = sum(fb_data["soreness"]) / len(fb_data["soreness"])
        else:
            avg_soreness = 1.0  # Default: moderate assumption

        if fb_data and fb_data["pump"]:
            avg_pump = sum(fb_data["pump"]) / len(fb_data["pump"])
        else:
            avg_pump = 1.5  # Default: moderate assumption

        if fb_data and fb_data["volume"]:
            avg_volume = sum(fb_data["volume"]) / len(fb_data["volume"])
        else:
            avg_volume = 0.0  # Default: just right

        recovery_state = classify_recovery_state(avg_soreness)
        stimulus_quality = classify_stimulus_quality(avg_pump, avg_volume)

        # ── Get previous session data for this exercise ──
        # Find the most recent completed occurrence of this exercise for this user
        prev_sets_data = []
        if user_id:
            prev_mde = (
                db.query(models.MesocycleDayExercise)
                .join(models.MesocycleDay)
                .join(models.MesocycleWeek)
                .join(models.Mesocycle)
                .filter(
                    models.Mesocycle.user_id == user_id,
                    models.MesocycleDayExercise.exercise_id == mde.exercise_id,
                    models.MesocycleDay.is_completed == True,
                    models.MesocycleDayExercise.id != mde.id,  # Exclude current
                )
                .options(joinedload(models.MesocycleDayExercise.set_logs))
                .order_by(models.MesocycleDayExercise.id.desc())
                .first()
            )

            if prev_mde and prev_mde.set_logs:
                for sl in sorted(prev_mde.set_logs, key=lambda s: s.set_number):
                    if sl.weight > 0:  # Skip skipped sets
                        prev_sets_data.append({
                            "set_number": sl.set_number,
                            "weight": sl.weight,
                            "reps": sl.reps,
                        })

        # ── Calculate per-set targets ──
        set_targets = []

        for set_num in range(1, mde.prescribed_sets + 1):
            # Find the matching set from previous session
            prev_set = next(
                (s for s in prev_sets_data if s["set_number"] == set_num),
                None
            )

            if prev_set and prev_set["weight"] > 0:
                # We have history for this set — apply double progression
                target = calculate_set_target(
                    last_weight=prev_set["weight"],
                    last_reps=prev_set["reps"],
                    is_dumbbell=is_db,
                    recovery_state=recovery_state,
                    stimulus_quality=stimulus_quality,
                )
                set_targets.append({
                    "set_number": set_num,
                    "target_weight": target["target_weight"],
                    "target_reps": target["target_reps"],
                    "action": target["action"],
                    "reason": target["reason"],
                    "source": "history",
                })

            elif prev_sets_data:
                # No data for this specific set number (maybe it's a new set)
                # Use the average of existing sets as a starting point
                valid_sets = [s for s in prev_sets_data if s["weight"] > 0]
                if valid_sets:
                    avg_weight = sum(s["weight"] for s in valid_sets) / len(valid_sets)
                    avg_reps = int(
                        sum(s["reps"] for s in valid_sets) / len(valid_sets)
                    )
                    set_targets.append({
                        "set_number": set_num,
                        "target_weight": round(avg_weight, 1),
                        "target_reps": avg_reps,
                        "action": "new_set",
                        "reason": (
                            f"New set added. Starting at average of previous "
                            f"sets: {avg_weight:.1f}kg × {avg_reps} reps."
                        ),
                        "source": "autofill",
                    })
                else:
                    set_targets.append({
                        "set_number": set_num,
                        "target_weight": 0,
                        "target_reps": DEFAULT_REP_FLOOR,
                        "action": "initialize",
                        "reason": "No usable previous data. Enter your working weight.",
                        "source": "no_data",
                    })

            else:
                # No history at all — check autofill from any previous occurrence
                if user_id:
                    autofill = get_last_weight_for_exercise(
                        db, mde.exercise_id, user_id
                    )
                    if autofill and autofill["weight"]:
                        set_targets.append({
                            "set_number": set_num,
                            "target_weight": autofill["weight"],
                            "target_reps": autofill.get("reps", DEFAULT_REP_FLOOR),
                            "action": "autofill",
                            "reason": (
                                f"No session history found. Using last logged weight: "
                                f"{autofill['weight']}kg × {autofill.get('reps', DEFAULT_REP_FLOOR)}."
                            ),
                            "source": "autofill",
                        })
                    else:
                        set_targets.append({
                            "set_number": set_num,
                            "target_weight": 0,
                            "target_reps": DEFAULT_REP_FLOOR,
                            "action": "initialize",
                            "reason": (
                                "First time doing this exercise. "
                                "Enter your working weight."
                            ),
                            "source": "no_data",
                        })
                else:
                    set_targets.append({
                        "set_number": set_num,
                        "target_weight": 0,
                        "target_reps": DEFAULT_REP_FLOOR,
                        "action": "initialize",
                        "reason": "No data available.",
                        "source": "no_data",
                    })

        results.append({
            "mde_id": mde.id,
            "exercise_id": mde.exercise_id,
            "exercise_name": exercise_name,
            "muscle_group": muscle_group,
            "equipment": equipment or "unknown",
            "is_dumbbell": is_db,
            "prescribed_sets": mde.prescribed_sets,
            "recovery_state": recovery_state,
            "stimulus_quality": stimulus_quality,
            "feedback_summary": {
                "avg_soreness": round(avg_soreness, 2),
                "avg_pump": round(avg_pump, 2),
                "avg_volume_feeling": round(avg_volume, 2),
            },
            "set_targets": set_targets,
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# SET PERFORMANCE EVALUATION
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_set_performance(
    target_weight: float,
    target_reps: int,
    actual_weight: float,
    actual_reps: int
) -> str:
    """
    Evaluate actual performance against targets.

    Compares the volume load (weight × reps) and individual components
    to produce a simple verdict.

    Args:
        target_weight: Prescribed target weight
        target_reps: Prescribed target reps
        actual_weight: What the user actually lifted
        actual_reps: How many reps the user actually completed

    Returns:
        One of:
            'exceeded'  — beat the target on both weight and reps
            'hit'       — met the target (within tolerance)
            'partial'   — met one dimension but not the other
            'missed'    — fell short on both
    """
    if target_weight <= 0 or target_reps <= 0:
        return "hit"  # No target to compare against

    weight_met = actual_weight >= target_weight
    reps_met = actual_reps >= target_reps

    # Calculate volume load comparison
    target_volume = target_weight * target_reps
    actual_volume = actual_weight * actual_reps

    if weight_met and reps_met:
        if actual_weight > target_weight and actual_reps > target_reps:
            return "exceeded"
        return "hit"

    elif weight_met or reps_met:
        # One dimension met — check if overall volume is close
        if actual_volume >= target_volume * 0.95:
            return "hit"  # Volume-equivalent performance
        return "partial"

    else:
        # Both missed — but how badly?
        if actual_volume >= target_volume * 0.90:
            return "partial"  # Close enough to not be alarming
        return "missed"
