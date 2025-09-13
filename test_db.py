from app.database import SessionLocal
from app import crud, models

# --------------------------
# Connect to DB
# --------------------------
db = SessionLocal()
print("Connected to PostgreSQL successfully!")

# --------------------------
# Test user
# --------------------------
existing_user = crud.get_user_by_email(db, "test@example.com")
if existing_user:
    print(f"User already exists: {existing_user.id} | {existing_user.name}")
    test_user = existing_user
else:
    test_user = crud.create_user(db, name="Test User", email="test@example.com", password="password123")
    print(f"Created user: {test_user.id} | {test_user.name}")

# --------------------------
# Test workout
# --------------------------
# Check if workout already exists
existing_workout = db.query(models.Workout).filter(models.Workout.name == "Test Workout").first()
if existing_workout:
    print(f"Workout already exists: {existing_workout.id} | {existing_workout.name}")
    test_workout = existing_workout
else:
    test_workout = crud.create_workout(
        db,
        name="Test Workout",
        default_sets=3,
        default_reps=10,
        default_load=50.0
    )
    print(f"Created workout: {test_workout.id} | {test_workout.name}")

# --------------------------
# Test logging a workout
# --------------------------
from random import choice

feedback_options = ["easy", "just right", "hard"]

test_log = crud.log_user_workout(
    db,
    user_id=test_user.id,
    workout_id=test_workout.id,
    sets=3,
    reps=10,
    load=50.0,
    feedback=choice(feedback_options)
)
print(f"Logged workout: {test_log.id} | User: {test_user.name} | Workout: {test_workout.name} | Feedback: {test_log.feedback}")

# --------------------------
# Close DB session
# --------------------------
db.close()
print("Database session closed.")
