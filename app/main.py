# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import engine, SessionLocal
from app.models import Base, User
from app import schemas, crud, models
from app.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)


# ─── Create all tables ───────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────
app = FastAPI(
    title="Iron Protocol API",
    description="Systematic destruction. Calculated growth.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Dependencies ─────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    if payload.get("type") != "access":
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

# ═════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════
@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, name=user_in.name, email=user_in.email, password=user_in.password)
    return user

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user.id), "type": "access"})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "type": "refresh"})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@app.post("/auth/refresh")
def refresh_token(body: schemas.RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    new_access = create_access_token(data={"sub": user_id, "type": "access"})
    return {"access_token": new_access, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ═════════════════════════════════════════════════════════
# EXERCISE ROUTES
# ═════════════════════════════════════════════════════════
@app.get("/exercises/", response_model=List[schemas.ExerciseResponse])
def list_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    body_part: Optional[str] = None,
    target: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_exercises(db, skip=skip, limit=limit,
                              body_part=body_part, target=target, search=search)

@app.get("/exercises/{exercise_id}", response_model=schemas.ExerciseResponse)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ex = crud.get_exercise_by_id(db, exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ex

# ═════════════════════════════════════════════════════════
# PLAN ROUTES
# ═════════════════════════════════════════════════════════
@app.post("/plans/", response_model=schemas.PlanResponse)
def create_plan(
    plan_in: schemas.PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    days_data = []
    for d in plan_in.days:
        day_dict = {"name": d.name, "order": d.order, "exercises": []}
        for ex in d.exercises:
            day_dict["exercises"].append({
                "exercise_id": ex.exercise_id,
                "order": ex.order,
            })
        days_data.append(day_dict)

    plan = crud.create_plan(db, user_id=current_user.id, name=plan_in.name, days_data=days_data)
    return crud.get_plan_by_id(db, plan.id, current_user.id)

@app.get("/plans/", response_model=List[schemas.PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_plans(db, current_user.id)

@app.get("/plans/{plan_id}", response_model=schemas.PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@app.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = crud.delete_plan(db, plan_id, current_user.id)
    if result == "in_use":
        raise HTTPException(status_code=400,
                            detail="Cannot delete — plan is used by one or more mesocycles")
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"detail": "Plan deleted"}

# ═════════════════════════════════════════════════════════
# MESOCYCLE ROUTES
# ═════════════════════════════════════════════════════════
@app.post("/mesocycles/", response_model=schemas.MesocycleResponse)
def start_mesocycle(
    meso_in: schemas.MesocycleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meso = crud.start_mesocycle(db, user_id=current_user.id,
                                plan_id=meso_in.plan_id, name=meso_in.name)
    if not meso:
        raise HTTPException(status_code=404, detail="Plan not found or not yours")
    return meso

@app.get("/mesocycles/", response_model=List[schemas.MesocycleResponse])
def list_mesocycles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_mesocycles(db, current_user.id)

@app.get("/mesocycles/{mesocycle_id}")
def get_mesocycle(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meso = crud.get_mesocycle_detail(db, mesocycle_id, current_user.id)
    if not meso:
        raise HTTPException(status_code=404, detail="Mesocycle not found")

    weeks_out = []
    for week in sorted(meso.weeks, key=lambda w: w.week_number):
        days_out = []
        for day in sorted(week.days, key=lambda d: d.day_order):
            day_name = day.plan_day.name if day.plan_day else f"Day {day.day_order}"
            days_out.append({
                "id": day.id,
                "plan_day_id": day.plan_day_id,
                "day_order": day.day_order,
                "is_completed": day.is_completed,
                "day_name": day_name,
                "exercises": [
                    {
                        "id": mde.id,
                        "exercise_id": mde.exercise_id,
                        "exercise_order": mde.exercise_order,
                        "prescribed_sets": mde.prescribed_sets,
                        "prescribed_reps": mde.prescribed_reps,
                        "note": mde.note,
                        "exercise": {
                            "id": mde.exercise.id,
                            "name": mde.exercise.name,
                            "body_part": mde.exercise.body_part,
                            "equipment": mde.exercise.equipment,
                            "target": mde.exercise.target,
                        },
                        "set_logs": [
                            {
                                "id": sl.id,
                                "set_number": sl.set_number,
                                "weight": sl.weight,
                                "reps": sl.reps,
                                "logged_at": sl.logged_at.isoformat() if sl.logged_at else None,
                            }
                            for sl in sorted(mde.set_logs, key=lambda s: s.set_number)
                        ],
                    }
                    for mde in sorted(day.exercises, key=lambda e: e.exercise_order)
                ],
                "feedbacks": [
                    {
                        "id": fb.id,
                        "muscle_group": fb.muscle_group,
                        "soreness": fb.soreness.value if hasattr(fb.soreness, 'value') else fb.soreness,
                        "pump": fb.pump.value if hasattr(fb.pump, 'value') else fb.pump,
                        "volume_feeling": fb.volume_feeling.value if hasattr(fb.volume_feeling, 'value') else fb.volume_feeling,
                        "notes": fb.notes,
                    }
                    for fb in day.feedbacks
                ],
            })
        weeks_out.append({
            "id": week.id,
            "week_number": week.week_number,
            "days": days_out,
        })

    return {
        "id": meso.id,
        "plan_id": meso.plan_id,
        "name": meso.name,
        "current_week": meso.current_week,
        "is_active": meso.is_active,
        "started_at": meso.started_at.isoformat() if meso.started_at else None,
        "weeks": weeks_out,
    }

@app.delete("/mesocycles/{mesocycle_id}")
def delete_mesocycle(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = crud.delete_mesocycle(db, mesocycle_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Mesocycle not found")
    return {"detail": "Mesocycle deleted"}

# ── Current workout ───────────────────────────────────
@app.get("/mesocycles/{mesocycle_id}/current-workout", response_model=schemas.MesocycleDayResponse)
def current_workout(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    day = crud.get_current_workout(db, mesocycle_id, current_user.id)
    if not day:
        raise HTTPException(status_code=404,
                            detail="No incomplete workout found — week may be complete")
    return day

# ── Log a set ─────────────────────────────────────────
@app.post("/mesocycle-day-exercises/{mde_id}/log-set", response_model=schemas.SetLogResponse)
def log_set(
    mde_id: int,
    set_in: schemas.SetLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sl = crud.log_set(db, meso_day_exercise_id=mde_id,
                      set_number=set_in.set_number,
                      weight=set_in.weight, reps=set_in.reps)
    return sl

# ── Skip sets ─────────────────────────────────────────
@app.post("/mesocycle-day-exercises/{mde_id}/skip-sets")
def skip_sets(
    mde_id: int,
    body: schemas.SkipSetsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud.skip_sets(db, mde_id, body.from_set, body.to_set)
    return {"detail": f"Sets {body.from_set}-{body.to_set} skipped"}

# ── Add set to exercise ──────────────────────────────
@app.post("/mesocycle-day-exercises/{mde_id}/add-set")
def add_set(
    mde_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mde = crud.add_set_to_exercise(db, mde_id)
    if not mde:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {"prescribed_sets": mde.prescribed_sets}

# ── Save note ─────────────────────────────────────────
@app.post("/mesocycle-day-exercises/{mde_id}/note")
def save_note(
    mde_id: int,
    body: schemas.ExerciseNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mde = crud.save_exercise_note(db, mde_id, body.note)
    if not mde:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {"detail": "Note saved", "note": mde.note}

# ── Exercise history ──────────────────────────────────
@app.get("/exercises/{exercise_id}/history", response_model=List[schemas.ExerciseHistoryItem])
def exercise_history(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_exercise_history(db, exercise_id, current_user.id)

# ── Autofill (last weight) ───────────────────────────
@app.get("/exercises/{exercise_id}/autofill")
def autofill_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = crud.get_last_weight_for_exercise(db, exercise_id, current_user.id)
    if not result:
        return {"weight": None, "reps": None}
    return result

# ── Submit feedback ───────────────────────────────────
@app.post("/mesocycle-days/{meso_day_id}/feedback", response_model=schemas.FeedbackResponse)
def submit_feedback(
    meso_day_id: int,
    fb_in: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fb = crud.create_feedback(
        db,
        meso_day_id=meso_day_id,
        muscle_group=fb_in.muscle_group,
        soreness=fb_in.soreness.value,
        pump=fb_in.pump.value,
        volume_feeling=fb_in.volume_feeling.value,
        notes=fb_in.notes,
    )
    return fb

# ── Complete a day ────────────────────────────────────
@app.post("/mesocycle-days/{meso_day_id}/complete")
def complete_day(
    meso_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    day = crud.complete_day(db, meso_day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    return {"detail": "Day completed", "meso_day_id": meso_day_id}

# ── Per-day progression preview ───────────────────────
@app.get("/mesocycle-days/{meso_day_id}/progression",
         response_model=List[schemas.ProgressionRecommendation])
def get_progression(
    meso_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.calculate_progression(db, meso_day_id)

# ═════════════════════════════════════════════════════════
# FEEDBACK-DRIVEN PROGRESSION (Week-Level Intelligence)
# ═════════════════════════════════════════════════════════
@app.get("/mesocycles/{mesocycle_id}/feedback-progression",
         response_model=List[schemas.ProgressionDecision])
def get_feedback_progression(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    decisions = crud.calculate_feedback_driven_progression(db, mesocycle_id, current_user.id)
    if not decisions:
        raise HTTPException(
            status_code=404,
            detail="No feedback data found for the current week"
        )
    return decisions

@app.post("/mesocycles/{mesocycle_id}/apply-progression")
def apply_feedback_progression(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    decisions = crud.calculate_feedback_driven_progression(db, mesocycle_id, current_user.id)
    if not decisions:
        raise HTTPException(
            status_code=400,
            detail="No feedback data to base progression on"
        )

    result = crud.apply_feedback_progression(db, mesocycle_id, current_user.id, decisions)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Could not apply — next week may not exist yet. Advance the week first."
        )

    return {
        "detail": f"Progression applied — {result} exercise(s) adjusted",
        "adjustments_made": result,
        "decisions": decisions,
    }

# ═════════════════════════════════════════════════════════
# SMART PROGRESSION TARGETS
# ═════════════════════════════════════════════════════════

@app.get("/mesocycle-days/{meso_day_id}/smart-targets")
def get_smart_targets(
    meso_day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns per-exercise, per-set target recommendations (shadow text values).
    Called when workout page loads to populate ghost/shadow inputs.
    """
    # Verify ownership
    meso_day = db.query(models.MesocycleDay).join(
        models.MesocycleWeek
    ).join(
        models.Mesocycle
    ).filter(
        models.MesocycleDay.id == meso_day_id,
        models.Mesocycle.user_id == current_user.id
    ).first()

    if not meso_day:
        raise HTTPException(status_code=404, detail="Day not found")

    targets = crud.calculate_smart_progression(db, meso_day_id)

    return {
        "meso_day_id": meso_day_id,
        "week_number": meso_day.mesocycle_week.week_number if hasattr(meso_day, 'mesocycle_week') and meso_day.mesocycle_week else 1,
        "targets": targets
    }

@app.post("/mesocycle-days/{meso_day_id}/smart-targets")
def get_smart_targets_with_soreness(
    meso_day_id: int,
    soreness_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get smart progression targets with explicit soreness overrides.
    Body: {"muscle_group": "soreness_level", ...}
    """
    meso_day = db.query(models.MesocycleDay).join(
        models.MesocycleWeek
    ).join(
        models.Mesocycle
    ).filter(
        models.MesocycleDay.id == meso_day_id,
        models.Mesocycle.user_id == current_user.id
    ).first()

    if not meso_day:
        raise HTTPException(status_code=404, detail="Day not found")

    targets = crud.calculate_smart_progression(db, meso_day_id, soreness_overrides=soreness_data)

    return {
        "meso_day_id": meso_day_id,
        "week_number": meso_day.mesocycle_week.week_number if hasattr(meso_day, 'mesocycle_week') and meso_day.mesocycle_week else 1,
        "targets": targets
    }

@app.post("/sets/{set_log_id}/evaluate")
def evaluate_set(
    set_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    After logging a set, evaluate performance vs target.
    Returns: hit / improved / decreased
    """
    sl = db.query(models.SetLog).filter(models.SetLog.id == set_log_id).first()
    if not sl:
        raise HTTPException(status_code=404, detail="Set log not found")

    # Get the target for this set
    mde = db.query(models.MesocycleDayExercise).filter(
        models.MesocycleDayExercise.id == sl.meso_day_exercise_id
    ).options(
        joinedload(models.MesocycleDayExercise.meso_day)
    ).first()

    if not mde:
        return {"verdict": "hit", "detail": "No target data"}

    targets = crud.calculate_smart_progression(db, mde.meso_day_id)

    # Find the matching target
    target_weight = 0
    target_reps = 0
    for t in targets:
        if t["mde_id"] == mde.id:
            for st in t["set_targets"]:
                if st["set_number"] == sl.set_number:
                    target_weight = st["target_weight"]
                    target_reps = st["target_reps"]
                    break
            break

    verdict = crud.evaluate_set_performance(
        target_weight, target_reps, sl.weight, sl.reps
    )

    return {
        "verdict": verdict,
        "target_weight": target_weight,
        "target_reps": target_reps,
        "actual_weight": sl.weight,
        "actual_reps": sl.reps,
    }

# ── Advance to next week ─────────────────────────────
@app.post("/mesocycles/{mesocycle_id}/next-week", response_model=schemas.MesocycleResponse)
def advance_to_next_week(
    mesocycle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meso = crud.apply_progression_to_next_week(db, mesocycle_id, current_user.id)
    if not meso:
        raise HTTPException(
            status_code=400,
            detail="Cannot advance — either mesocycle not found or not all days are completed",
        )
    return meso
