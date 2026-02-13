# app/crud.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List, Dict
from app import models
from app.utils import hash_password
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

    delta_map = {d["muscle_group"]: d["delta"] for d in decisions}
    adjustments_made = 0

    for day in next_week.days:
        muscle_exercises: dict[str, list] = {}
        for mde in day.exercises:
            group = mde.exercise.body_part
            if group not in muscle_exercises:
                muscle_exercises[group] = []
            muscle_exercises[group].append(mde)

        for group, exercises in muscle_exercises.items():
            total_delta = delta_map.get(group, 0)
            if total_delta == 0:
                continue

            n_exercises = len(exercises)
            base_change = total_delta // n_exercises
            remainder = abs(total_delta) % n_exercises

            for i, mde in enumerate(exercises):
                if total_delta > 0:
                    adjustment = base_change + (1 if i < remainder else 0)
                else:
                    adjustment = base_change - (1 if i < remainder else 0)

                new_sets = max(1, mde.prescribed_sets + adjustment)
                if new_sets != mde.prescribed_sets:
                    mde.prescribed_sets = new_sets
                    adjustments_made += 1

    db.commit()
    return adjustments_made


# ═══════════════════════════════════════════════════════
# SMART PROGRESSION ENGINE
# ═══════════════════════════════════════════════════════

def _get_previous_session_feedback(db: Session, mesocycle_id: int, 
                                     muscle_group: str, current_week: int):
    """
    Get feedback from the PREVIOUS week's session that trained this muscle group.
    Returns the Feedback object or None.
    """
    if current_week <= 1:
        return None

    prev_week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == mesocycle_id,
            models.MesocycleWeek.week_number == current_week - 1,
        )
        .first()
    )
    if not prev_week:
        return None

    # Find a completed day in previous week that has feedback for this muscle group
    prev_days = (
        db.query(models.MesocycleDay)
        .filter(
            models.MesocycleDay.week_id == prev_week.id,
            models.MesocycleDay.is_completed == True,
        )
        .options(joinedload(models.MesocycleDay.feedbacks))
        .all()
    )

    for day in prev_days:
        for fb in day.feedbacks:
            if fb.muscle_group.lower() == muscle_group.lower():
                return fb

    return None


def _get_previous_session_sets(db: Session, mesocycle_id: int,
                                 exercise_id: int, current_week: int):
    """
    Get the set logs from the PREVIOUS week for this exercise.
    Returns list of SetLog objects sorted by set_number.
    """
    if current_week <= 1:
        return []

    prev_week = (
        db.query(models.MesocycleWeek)
        .filter(
            models.MesocycleWeek.mesocycle_id == mesocycle_id,
            models.MesocycleWeek.week_number == current_week - 1,
        )
        .first()
    )
    if not prev_week:
        return []

    prev_mde = (
        db.query(models.MesocycleDayExercise)
        .join(models.MesocycleDay)
        .filter(
            models.MesocycleDay.week_id == prev_week.id,
            models.MesocycleDayExercise.exercise_id == exercise_id,
        )
        .options(joinedload(models.MesocycleDayExercise.set_logs))
        .first()
    )
    if not prev_mde:
        return []

    return sorted(prev_mde.set_logs, key=lambda s: s.set_number)


def calculate_smart_progression(db: Session, meso_day_id: int):
    """
    The Iron Protocol Progression Engine.
    
    Cross-references TODAY's soreness with LAST SESSION's pump + volume_feeling
    to determine the exact progression type per muscle group, then generates
    per-set targets (shadow text values) for every exercise.
    
    Decision Matrix:
    ┌─────────────────────┬──────────────────────┬────────────────────────┬──────────────┐
    │ Today Soreness      │ Last Pump            │ Last Volume            │ Action       │
    ├─────────────────────┼──────────────────────┼────────────────────────┼──────────────┤
    │ severe              │ any                  │ too_much               │ DELOAD       │
    │ severe/moderate     │ any                  │ too_little/just_right  │ +REPS only   │
    │ none/light          │ moderate/great       │ just_right             │ +SET         │
    │ none/light          │ great                │ too_little             │ +SET +REPS   │
    │ none/light          │ none/light           │ just_right             │ +REPS        │
    │ none/light          │ none/light           │ too_little             │ +WEIGHT      │
    │ light               │ great                │ just_right             │ +REPS        │
    │ any                 │ any                  │ too_much               │ MAINTAIN     │
    └─────────────────────┴──────────────────────┴────────────────────────┴──────────────┘
    """
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

    meso = day.week.mesocycle
    current_week = day.week.week_number

    # Build today's soreness map from feedbacks already submitted today
    today_soreness_map = {}
    for fb in day.feedbacks:
        today_soreness_map[fb.muscle_group.lower()] = fb.soreness

    # Group exercises by muscle group
    muscle_groups = {}
    for mde in day.exercises:
        target = mde.exercise.target.lower()
        if target not in muscle_groups:
            muscle_groups[target] = []
        muscle_groups[target].append(mde)

    targets = []

    for muscle_group, exercises in muscle_groups.items():
        # ─── Gather signals ─────────────────────────
        today_soreness = today_soreness_map.get(muscle_group)
        prev_feedback = _get_previous_session_feedback(
            db, meso.id, muscle_group, current_week
        )

        # Soreness classification
        soreness_str = today_soreness
        if hasattr(today_soreness, 'value'):
            soreness_str = today_soreness.value
        high_soreness = soreness_str in ("moderate", "severe")
        severe_soreness = soreness_str == "severe"
        low_soreness = soreness_str in ("none", "light", None)

        # Previous session signals (default to neutral if week 1)
        if prev_feedback:
            prev_pump = prev_feedback.pump
            if hasattr(prev_pump, 'value'):
                prev_pump = prev_pump.value
            prev_volume = prev_feedback.volume_feeling
            if hasattr(prev_volume, 'value'):
                prev_volume = prev_volume.value
        else:
            prev_pump = "moderate"       # neutral default for week 1
            prev_volume = "just_right"   # neutral default for week 1

        good_pump = prev_pump in ("moderate", "great")
        great_pump = prev_pump == "great"
        weak_pump = prev_pump in ("none", "light")
        vol_ok = prev_volume == "just_right"
        vol_low = prev_volume == "too_little"
        vol_high = prev_volume == "too_much"

        # ─── Decision Matrix ────────────────────────
        if severe_soreness and vol_high:
            progression_type = "deload"
            reason = "Severe soreness + last session felt too much → deload to recover"
            rep_delta = -2
            add_new_set = False
            weight_bump = 0
        elif high_soreness and (vol_low or vol_ok):
            progression_type = "add_reps"
            reason = "High soreness but volume wasn't excessive → add reps only, no extra set"
            rep_delta = 1
            add_new_set = False
            weight_bump = 0
        elif high_soreness and vol_high:
            progression_type = "maintain"
            reason = "High soreness + volume was too much → maintain current, let body adapt"
            rep_delta = 0
            add_new_set = False
            weight_bump = 0
        elif low_soreness and good_pump and vol_ok:
            progression_type = "add_set"
            reason = "Low soreness + good pump + volume was right → add a set for overload"
            rep_delta = 0
            add_new_set = True
            weight_bump = 0
        elif low_soreness and great_pump and vol_low:
            progression_type = "add_set"
            reason = "Low soreness + great pump + volume felt low → add set + bump reps"
            rep_delta = 1
            add_new_set = True
            weight_bump = 0
        elif low_soreness and weak_pump and vol_ok:
            progression_type = "add_reps"
            reason = "Low soreness + weak pump + volume OK → add reps to drive more stimulus"
            rep_delta = 2
            add_new_set = False
            weight_bump = 0
        elif low_soreness and weak_pump and vol_low:
            progression_type = "add_weight"
            reason = "Low soreness + weak pump + felt too easy → bump weight for intensity"
            rep_delta = 0
            add_new_set = False
            weight_bump = 2.5  # kg increment
        elif low_soreness and good_pump and vol_high:
            progression_type = "maintain"
            reason = "Low soreness but volume felt high → maintain, adaptation in progress"
            rep_delta = 0
            add_new_set = False
            weight_bump = 0
        else:
            # Default: light soreness + great pump + vol ok → add reps
            progression_type = "add_reps"
            reason = "Good recovery + solid pump → progressive overload via reps"
            rep_delta = 1
            add_new_set = False
            weight_bump = 0

        # ─── Generate per-exercise targets ──────────
        for mde in exercises:
            prev_sets = _get_previous_session_sets(
                db, meso.id, mde.exercise_id, current_week
            )

            # Calculate how many total sets
            current_prescribed = mde.prescribed_sets
            total_sets = current_prescribed + (1 if add_new_set else 0)

            # If deloading, potentially reduce sets
            if progression_type == "deload":
                total_sets = max(1, current_prescribed - 1)

            set_targets = []
            for s in range(1, total_sets + 1):
                is_new = s > current_prescribed

                # Find matching previous set for reference
                prev_set = None
                if prev_sets:
                    for ps in prev_sets:
                        if ps.set_number == s:
                            prev_set = ps
                            break
                    # If new set, clone the last set's values
                    if not prev_set and prev_sets:
                        prev_set = prev_sets[-1]

                if prev_set and prev_set.weight > 0:
                    base_weight = prev_set.weight
                    base_reps = prev_set.reps
                else:
                    # No previous data — can't generate target
                    # Use current logged data if available
                    current_log = None
                    for sl in mde.set_logs:
                        if sl.set_number == s:
                            current_log = sl
                            break
                    if current_log and current_log.weight > 0:
                        base_weight = current_log.weight
                        base_reps = current_log.reps
                    else:
                        base_weight = 0
                        base_reps = 0

                target_weight = base_weight + weight_bump
                target_reps = max(1, base_reps + rep_delta) if base_reps > 0 else 0

                # For deload, reduce weight by ~10%
                if progression_type == "deload" and base_weight > 0:
                    target_weight = round(base_weight * 0.9 / 2.5) * 2.5  # Round to 2.5kg
                    target_reps = base_reps  # Keep reps same on deload

                set_targets.append({
                    "set_number": s,
                    "target_weight": target_weight,
                    "target_reps": target_reps,
                    "is_new_set": is_new,
                })

            targets.append({
                "mde_id": mde.id,
                "exercise_id": mde.exercise_id,
                "exercise_name": mde.exercise.name,
                "muscle_group": muscle_group,
                "progression_type": progression_type,
                "reason": reason,
                "prescribed_sets": total_sets,
                "set_targets": set_targets,
            })

    return targets


def evaluate_set_performance(target_weight: float, target_reps: int,
                               actual_weight: float, actual_reps: int) -> str:
    """
    Compare actual vs target and return verdict.
    
    Volume = weight × reps
    - improved: actual volume > target volume
    - hit: actual volume within 5% of target
    - decreased: actual volume < 95% of target
    """
    if target_weight == 0 or target_reps == 0:
        return "hit"  # No target available, neutral

    target_volume = target_weight * target_reps
    actual_volume = actual_weight * actual_reps

    if target_volume == 0:
        return "hit"

    ratio = actual_volume / target_volume

    if ratio >= 1.02:
        return "improved"
    elif ratio >= 0.95:
        return "hit"
    else:
        return "decreased"


# ═══════════════════════════════════════════════════════════════════════════════
# SMART PROGRESSION ENGINE - Per-Set Shadow Target System
# ═══════════════════════════════════════════════════════════════════════════════

def _get_previous_week_day(db: Session, meso_day: models.MesocycleDay) -> Optional[models.MesocycleDay]:
    """
    Find the equivalent day from the previous week.
    E.g., if this is Week 2, Day 1 -> find Week 1, Day 1
    """
    current_week = meso_day.week
    if current_week.week_number <= 1:
        return None
    
    # Find previous week
    previous_week = db.query(models.MesocycleWeek).filter(
        models.MesocycleWeek.mesocycle_id == current_week.mesocycle_id,
        models.MesocycleWeek.week_number == current_week.week_number - 1
    ).first()
    
    if not previous_week:
        return None
    
    # Find matching day by order
    previous_day = db.query(models.MesocycleDay).filter(
        models.MesocycleDay.week_id == previous_week.id,
        models.MesocycleDay.day_order == meso_day.day_order
    ).first()
    
    return previous_day


def _get_previous_session_feedback(
    db: Session, 
    previous_day: models.MesocycleDay, 
    muscle_group: str
) -> Optional[models.Feedback]:
    """Get feedback for a specific muscle group from the previous session."""
    return db.query(models.Feedback).filter(
        models.Feedback.meso_day_id == previous_day.id,
        models.Feedback.muscle_group == muscle_group
    ).first()


def _get_previous_session_sets(
    db: Session, 
    previous_day: models.MesocycleDay, 
    exercise_id: int
) -> List[models.SetLog]:
    """Get all logged sets for an exercise from the previous session."""
    # Find the MDE in previous day
    previous_mde = db.query(models.MesocycleDayExercise).filter(
        models.MesocycleDayExercise.meso_day_id == previous_day.id,
        models.MesocycleDayExercise.exercise_id == exercise_id
    ).first()
    
    if not previous_mde:
        return []
    
    return db.query(models.SetLog).filter(
        models.SetLog.mde_id == previous_mde.id
    ).order_by(models.SetLog.set_number).all()


def _get_current_day_soreness(
    db: Session, 
    current_day: models.MesocycleDay, 
    muscle_group: str
) -> Optional[str]:
    """
    Get TODAY's soreness for a muscle group.
    This might be submitted at start of workout or we check existing feedback.
    """
    feedback = db.query(models.Feedback).filter(
        models.Feedback.meso_day_id == current_day.id,
        models.Feedback.muscle_group == muscle_group
    ).first()
    
    if feedback:
        return feedback.soreness
    return None


def calculate_smart_progression(
    db: Session, 
    meso_day_id: int,
    soreness_overrides: Optional[dict] = None
) -> List[dict]:
    """
    SMART PROGRESSION ENGINE
    
    Cross-references:
    - Today's Soreness (current day)
    - Last Session's Pump + Volume Feeling (previous week, same day)
    
    Returns per-exercise progression targets with shadow set values.
    
    Decision Matrix:
    ┌─────────────┬───────────────────┬──────────────────┬──────────────────┐
    │ Soreness    │ Pump: Great       │ Pump: Moderate   │ Pump: Low/None   │
    │ (Today)     │ Vol: Just Right   │ Vol: Too Little  │ Vol: Too Much    │
    ├─────────────┼───────────────────┼──────────────────┼──────────────────┤
    │ None/Light  │ +Weight (2.5kg)   │ +Set             │ Maintain         │
    │ Moderate    │ +Reps (+2)        │ +Reps (+1)       │ Maintain         │
    │ Severe      │ Maintain          │ Deload (-10%)    │ Deload (-15%)    │
    └─────────────┴───────────────────┴──────────────────┴──────────────────┘
    """
    from app.schemas import ProgressionType
    
    meso_day = db.query(models.MesocycleDay).filter(
        models.MesocycleDay.id == meso_day_id
    ).first()
    
    if not meso_day:
        return []
    
    previous_day = _get_previous_week_day(db, meso_day)
    
    # Get all exercises for this day
    mdes = db.query(models.MesocycleDayExercise).filter(
        models.MesocycleDayExercise.meso_day_id == meso_day_id
    ).order_by(models.MesocycleDayExercise.exercise_order).all()
    
    results = []
    
    for mde in mdes:
        exercise = mde.exercise
        muscle_group = exercise.target.lower()
        
        # Get today's soreness (from override or existing feedback)
        if soreness_overrides and muscle_group in soreness_overrides:
            today_soreness = soreness_overrides[muscle_group]
        else:
            today_soreness = _get_current_day_soreness(db, meso_day, muscle_group)
        
        # Default progression values
        progression_type = ProgressionType.maintain
        reason = "Week 1 baseline - no previous data"
        weight_delta = 0.0
        rep_delta = 0
        deload_factor = 1.0
        add_new_set = False
        
        # Get previous session data if available
        previous_sets = []
        if previous_day:
            previous_sets = _get_previous_session_sets(db, previous_day, exercise.id)
            prev_feedback = _get_previous_session_feedback(db, previous_day, muscle_group)
            
            if prev_feedback and previous_sets:
                pump = prev_feedback.pump
                volume = prev_feedback.volume_feeling
                soreness = today_soreness or "none"
                
                # DECISION MATRIX IMPLEMENTATION
                soreness_low = soreness in ["none", "light"]
                soreness_mod = soreness == "moderate"
                soreness_severe = soreness == "severe"
                
                pump_great = pump == "great"
                pump_moderate = pump == "moderate"
                pump_low = pump in ["none", "light"]
                
                vol_right = volume == "just_right"
                vol_low = volume == "too_little"
                vol_high = volume == "too_much"
                
                # Row 1: No/Light Soreness
                if soreness_low:
                    if pump_great and vol_right:
                        progression_type = ProgressionType.add_weight
                        weight_delta = 2.5
                        reason = f"Great pump + good volume + fresh → +2.5kg"
                    elif pump_low or vol_low:
                        progression_type = ProgressionType.add_set
                        add_new_set = True
                        reason = f"Low stimulus detected → +1 set for more volume"
                    elif vol_high:
                        progression_type = ProgressionType.maintain
                        reason = f"Volume felt high but recovered well → maintain"
                    else:
                        progression_type = ProgressionType.add_reps
                        rep_delta = 1
                        reason = f"Moderate signals + recovered → +1 rep"
                
                # Row 2: Moderate Soreness
                elif soreness_mod:
                    if pump_great or vol_right:
                        progression_type = ProgressionType.add_reps
                        rep_delta = 2
                        reason = f"Good stimulus but still sore → +2 reps (no load increase)"
                    elif vol_low:
                        progression_type = ProgressionType.add_reps
                        rep_delta = 1
                        reason = f"Need more volume but sore → careful +1 rep"
                    else:
                        progression_type = ProgressionType.maintain
                        reason = f"Moderate soreness + high volume → maintain and recover"
                
                # Row 3: Severe Soreness
                elif soreness_severe:
                    if vol_high or pump_low:
                        progression_type = ProgressionType.deload
                        deload_factor = 0.85
                        reason = f"Severe soreness + overreached → deload 15%"
                    elif vol_low:
                        progression_type = ProgressionType.deload
                        deload_factor = 0.90
                        reason = f"Severe soreness → deload 10% despite low volume feel"
                    else:
                        progression_type = ProgressionType.maintain
                        reason = f"Severe soreness but signals mixed → maintain (recovery priority)"
        
        # Calculate set targets
        set_targets = []
        
        if previous_sets:
            # Base targets on previous performance
            for prev_set in previous_sets:
                target_weight = prev_set.weight
                target_reps = prev_set.reps
                
                # Apply progression adjustments
                if progression_type == ProgressionType.add_weight:
                    target_weight += weight_delta
                elif progression_type == ProgressionType.add_reps:
                    target_reps += rep_delta
                elif progression_type == ProgressionType.deload:
                    target_weight = round(target_weight * deload_factor, 1)
                
                set_targets.append({
                    "set_number": prev_set.set_number,
                    "target_weight": target_weight,
                    "target_reps": target_reps,
                    "is_new_set": False
                })
            
            # Add new set if prescribed
            if add_new_set:
                last_set = previous_sets[-1]
                set_targets.append({
                    "set_number": len(previous_sets) + 1,
                    "target_weight": last_set.weight,
                    "target_reps": max(last_set.reps - 2, 5),  # Slightly lower reps for new set
                    "is_new_set": True
                })
        else:
            # No previous data - create baseline targets
            # Use prescribed sets/reps or defaults
            for i in range(mde.prescribed_sets):
                set_targets.append({
                    "set_number": i + 1,
                    "target_weight": 0,  # User needs to establish
                    "target_reps": mde.prescribed_reps or 10,
                    "is_new_set": False
                })
        
        results.append({
            "mde_id": mde.id,
            "exercise_id": exercise.id,
            "exercise_name": exercise.name,
            "muscle_group": muscle_group,
            "progression_type": progression_type.value,
            "reason": reason,
            "prescribed_sets": mde.prescribed_sets,
            "set_targets": set_targets
        })
    
    return results


def evaluate_set_performance(
    db: Session,
    set_log_id: int
) -> dict:
    """
    Evaluate a logged set against its target.
    
    Compares: actual_volume vs target_volume
    Volume = weight × reps
    
    Returns verdict: 'hit' (within 5%), 'improved' (>5% better), 'decreased' (>5% worse)
    """
    from app.schemas import SetPerformanceVerdict
    
    set_log = db.query(models.SetLog).filter(models.SetLog.id == set_log_id).first()
    if not set_log:
        return {"error": "Set not found"}
    
    mde = set_log.mesocycle_day_exercise
    meso_day = mde.mesocycle_day
    
    # Get targets for this day
    targets = calculate_smart_progression(db, meso_day.id)
    
    # Find target for this exercise
    exercise_target = None
    for t in targets:
        if t["mde_id"] == mde.id:
            exercise_target = t
            break
    
    if not exercise_target:
        return {
            "verdict": SetPerformanceVerdict.hit.value,
            "target_weight": set_log.weight,
            "target_reps": set_log.reps,
            "actual_weight": set_log.weight,
            "actual_reps": set_log.reps,
            "note": "No target data available"
        }
    
    # Find specific set target
    set_target = None
    for st in exercise_target["set_targets"]:
        if st["set_number"] == set_log.set_number:
            set_target = st
            break
    
    if not set_target or set_target["target_weight"] == 0:
        return {
            "verdict": SetPerformanceVerdict.hit.value,
            "target_weight": set_log.weight,
            "target_reps": set_log.reps,
            "actual_weight": set_log.weight,
            "actual_reps": set_log.reps,
            "note": "Baseline set - no comparison"
        }
    
    # Calculate volumes
    target_volume = set_target["target_weight"] * set_target["target_reps"]
    actual_volume = set_log.weight * set_log.reps
    
    # Determine verdict
    if target_volume == 0:
        verdict = SetPerformanceVerdict.hit
    else:
        ratio = actual_volume / target_volume
        if ratio >= 1.05:
            verdict = SetPerformanceVerdict.improved
        elif ratio <= 0.95:
            verdict = SetPerformanceVerdict.decreased
        else:
            verdict = SetPerformanceVerdict.hit
    
    return {
        "verdict": verdict.value,
        "target_weight": set_target["target_weight"],
        "target_reps": set_target["target_reps"],
        "actual_weight": set_log.weight,
        "actual_reps": set_log.reps
    }


def get_exercise_history_for_progression(
    db: Session,
    user_id: int,
    exercise_id: int,
    limit: int = 10
) -> List[dict]:
    """
    Get recent performance history for an exercise across all mesocycles.
    Useful for long-term progression tracking.
    """
    # Get all MDEs for this exercise across user's mesocycles
    history = db.query(models.SetLog).join(
        models.MesocycleDayExercise
    ).join(
        models.MesocycleDay
    ).join(
        models.MesocycleWeek
    ).join(
        models.Mesocycle
    ).filter(
        models.Mesocycle.user_id == user_id,
        models.MesocycleDayExercise.exercise_id == exercise_id
    ).order_by(
        models.SetLog.logged_at.desc()
    ).limit(limit * 5).all()  # Get more to group by session
    
    # Group by session and calculate estimated 1RM
    sessions = {}
    for log in history:
        session_key = log.logged_at.date()
        if session_key not in sessions:
            sessions[session_key] = {
                "date": session_key.isoformat(),
                "sets": [],
                "best_set_volume": 0,
                "estimated_1rm": 0
            }
        
        volume = log.weight * log.reps
        sessions[session_key]["sets"].append({
            "weight": log.weight,
            "reps": log.reps,
            "volume": volume
        })
        
        if volume > sessions[session_key]["best_set_volume"]:
            sessions[session_key]["best_set_volume"] = volume
            # Brzycki formula for estimated 1RM
            if log.reps < 37:
                e1rm = log.weight * (36 / (37 - log.reps))
                sessions[session_key]["estimated_1rm"] = round(e1rm, 1)
    
    # Convert to list and sort
    result = list(sessions.values())
    result.sort(key=lambda x: x["date"], reverse=True)
    
    return result[:limit]
