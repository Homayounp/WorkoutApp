"""safe default workout

Revision ID: e506a37dca83
Revises: c907d64ed670
Create Date: 2025-09-11 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer

# revision identifiers, used by Alembic.
revision = 'e506a37dca83'
down_revision = 'c907d64ed670'
branch_labels = None
depends_on = None

def upgrade():
    # 1️⃣ Ensure a default workout exists
    workouts_table = table(
        'workouts',
        column('id', Integer),
        column('name', sa.String),
    )

    # Insert a default workout if none exists
    op.execute("""
        INSERT INTO workouts (name, default_sets, default_reps, default_load)
        SELECT 'Default Workout', 3, 10, 0
        WHERE NOT EXISTS (SELECT 1 FROM workouts WHERE name='Default Workout');
    """)

    # 2️⃣ Get the ID of the default workout
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM workouts WHERE name='Default Workout' LIMIT 1"))
    default_workout_id = result.scalar()

    # 3️⃣ Update null workout_id in user_logs
    user_logs_table = table(
        'user_logs',
        column('workout_id', Integer)
    )
    op.execute(
        user_logs_table.update()
        .where(user_logs_table.c.workout_id == None)
        .values(workout_id=default_workout_id)
    )

    # 4️⃣ Alter column to NOT NULL
    op.alter_column('user_logs', 'workout_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)

def downgrade():
    # Optional: revert NOT NULL constraint
    op.alter_column('user_logs', 'workout_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
