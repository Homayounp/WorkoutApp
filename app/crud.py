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


# Update a workout log
def update_workout_log(db: Session, log_id: int, sets: int = None, reps: int = None, load: float = None, feedback: str = None):
    log = db.query(models.WorkoutLog).filter(models.WorkoutLog.id == log_id).first()
    if not log:
        return None
    
    if sets is not None:
        log.sets = sets
    if reps is not None:
        log.reps = reps
    if load is not None:
        log.load = load
    if feedback is not None:
        log.feedback = feedback

    db.commit()
    db.refresh(log)
    return log


# Delete a workout log
def delete_workout_log(db: Session, log_id: int):
    log = db.query(models.WorkoutLog).filter(models.WorkoutLog.id == log_id).first()
    if not log:
        return None
    
    db.delete(log)
    db.commit()
    return log


# Update a workout
def update_workout(db: Session, workout_id: int, name: str = None, description: str = None, default_sets: int = None, default_reps: int = None, default_load: float = None):
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not workout:
        return None
    
    if name is not None:
        workout.name = name
    if description is not None:
        workout.description = description
    if default_sets is not None:
        workout.default_sets = default_sets
    if default_reps is not None:
        workout.default_reps = default_reps
    if default_load is not None:
        workout.default_load = default_load

    db.commit()
    db.refresh(workout)
    return workout


# Delete a workout
def delete_workout(db: Session, workout_id: int):
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not workout:
        return None
    
    db.delete(workout)
    db.commit()
    return workout

def get_user_logs(db: Session, user_id: int):
    return (
        db.query(models.WorkoutLog)
        .filter(models.WorkoutLog.user_id == user_id)
        .join(models.Workout)
        .all()
    )
