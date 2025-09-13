from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
from sqlalchemy import Integer, String

# Revision identifiers, used by Alembic.
revision = '2202f4712368'
down_revision = '579fbf1df0d0'
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()

    # ---- Ensure at least one default workout exists ----
    workout_result = connection.execute(sa.text("SELECT id FROM workouts LIMIT 1"))
    default_workout = workout_result.scalar()
    if default_workout is None:
        connection.execute(
            sa.text(
                "INSERT INTO workouts (name, default_sets, default_reps, default_load, description) "
                "VALUES (:n, :s, :r, :l, :d)"
            ),
            {"n": "Default Workout", "s": 3, "r": 10, "l": 0, "d": "Auto-created default workout"}
        )
        default_workout = connection.execute(
            sa.text("SELECT id FROM workouts WHERE name='Default Workout' LIMIT 1")
        ).scalar()

    # ---- Ensure at least one default user exists ----
    user_result = connection.execute(sa.text("SELECT id FROM users LIMIT 1"))
    default_user = user_result.scalar()
    if default_user is None:
        connection.execute(
            sa.text(
                "INSERT INTO users (name, email, password) VALUES (:n, :e, :p)"
            ),
            {"n": "Default User", "e": "default@example.com", "p": "password123"}
        )
        default_user = connection.execute(
            sa.text("SELECT id FROM users WHERE email='default@example.com' LIMIT 1")
        ).scalar()

    # ---- Fill NULLs in user_logs with valid foreign keys ----
    connection.execute(
        sa.text("UPDATE user_logs SET workout_id = :wid WHERE workout_id IS NULL"),
        {"wid": default_workout}
    )
    connection.execute(
        sa.text("UPDATE user_logs SET user_id = :uid WHERE user_id IS NULL"),
        {"uid": default_user}
    )

    # ---- Set columns to NOT NULL safely ----
    op.alter_column('user_logs', 'workout_id', existing_type=Integer, nullable=False)
    op.alter_column('user_logs', 'user_id', existing_type=Integer, nullable=False)
    op.alter_column('user_logs', 'sets', existing_type=Integer, nullable=False)
    op.alter_column('user_logs', 'reps', existing_type=Integer, nullable=False)
    op.alter_column('user_logs', 'load', existing_type=Integer, nullable=False)

    # Example for users table
    op.alter_column('users', 'name', existing_type=sa.String(), nullable=False)
    op.alter_column('users', 'email', existing_type=sa.String(), nullable=False)
    op.alter_column('users', 'password', existing_type=sa.String(), nullable=False)

    # Example for workouts table
    op.alter_column('workouts', 'name', existing_type=sa.String(), nullable=False)
    op.alter_column('workouts', 'default_sets', existing_type=Integer, nullable=False)
    op.alter_column('workouts', 'default_reps', existing_type=Integer, nullable=False)
    op.alter_column('workouts', 'default_load', existing_type=Integer, nullable=False)
    # If description column is added and should allow NULLs, skip altering it

def downgrade():
    # Reverse NOT NULL constraints
    op.alter_column('user_logs', 'workout_id', existing_type=Integer, nullable=True)
    op.alter_column('user_logs', 'user_id', existing_type=Integer, nullable=True)
    op.alter_column('user_logs', 'sets', existing_type=Integer, nullable=True)
    op.alter_column('user_logs', 'reps', existing_type=Integer, nullable=True)
    op.alter_column('user_logs', 'load', existing_type=Integer, nullable=True)

    op.alter_column('users', 'name', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'email', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'password', existing_type=sa.String(), nullable=True)

    op.alter_column('workouts', 'name', existing_type=sa.String(), nullable=True)
    op.alter_column('workouts', 'default_sets', existing_type=Integer, nullable=True)
    op.alter_column('workouts', 'default_reps', existing_type=Integer, nullable=True)
    op.alter_column('workouts', 'default_load', existing_type=Integer, nullable=True)
