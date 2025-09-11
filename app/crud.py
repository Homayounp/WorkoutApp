from sqlalchemy.orm import Session
from app import models


def create_user(db: Session, name: str, email: str, password: str):
    new_user = models.User(name=name, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_workout(db: Session, name: str, default_sets: int, default_reps: int, default_load: float):
    workout = models.Workout(
        name=name, 
        default_sets=default_sets, 
        default_reps=default_reps, 
        default_load=default_load
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout

def log_user_workout(db: Session, user_id: int, workout_id: int, sets: int, reps: int, load: float, feedback: str):
    log = models.UserLog(
        user_id=user_id,
        workout_id=workout_id,
        sets=sets,
        reps=reps,
        load=load,
        feedback=feedback
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_user_logs(db: Session, user_id: int):
    return db.query(models.UserLog).filter(models.UserLog.user_id == user_id).all()
