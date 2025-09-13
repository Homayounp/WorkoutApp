"""Safe NOT NULL migration for user_logs, users, and workouts"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select

# revision identifiers, used by Alembic.
revision = 'safe_not_null'
down_revision = '579fbf1df0d0'
branch_labels = None
depends_on = None


def ensure_not_null(table_name, column_name, default=None, fk_table=None, fk_column='id'):
    """
    Set a column to NOT NULL safely, handling foreign keys and NULL values.
    """
    connection = op.get_bind()

    # If it's a foreign key column, ensure a valid row exists in the referenced table
    if fk_table:
        result = connection.execute(sa.text(f"SELECT {fk_column} FROM {fk_table} LIMIT 1"))
        default_value = result.scalar()
        if default_value is None:
            # Insert a default row in the fk_table if none exists
            connection.execute(sa.text(f"INSERT INTO {fk_table} ({fk_column}) VALUES (DEFAULT)"))
            default_value = connection.execute(sa.text(f"SELECT {fk_column} FROM {fk_table} LIMIT 1")).scalar()
    else:
        default_value = default

    # Fill NULLs with the default_value
    connection.execute(
        sa.text(f"UPDATE {table_name} SET {column_name} = :val WHERE {column_name} IS NULL"),
        {"val": default_value}
    )

    # Alter column to NOT NULL
    op.alter_column(table_name, column_name, existing_type=sa.Integer(), nullable=False)


def upgrade():
    # user_logs table
    ensure_not_null('user_logs', 'workout_id', fk_table='workouts')
    ensure_not_null('user_logs', 'user_id', fk_table='users')
    ensure_not_null('user_logs', 'sets', default=3)
    ensure_not_null('user_logs', 'reps', default=10)
    ensure_not_null('user_logs', 'load', default=0)

    # users table
    ensure_not_null('users', 'name', default='Default User')
    ensure_not_null('users', 'email', default='default@example.com')
    ensure_not_null('users', 'password', default='password123')

    # workouts table
    ensure_not_null('workouts', 'name', default='Default Workout')
    ensure_not_null('workouts', 'default_sets', default=3)
    ensure_not_null('workouts', 'default_reps', default=10)
    ensure_not_null('workouts', 'default_load', default=0)


def downgrade():
    # Revert NOT NULL constraints
    op.alter_column('user_logs', 'workout_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_logs', 'user_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_logs', 'sets', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_logs', 'reps', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_logs', 'load', existing_type=sa.Integer(), nullable=True)

    op.alter_column('users', 'name', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'email', existing_type=sa.String(), nullable=True)
    op.alter_column('users', 'password', existing_type=sa.String(), nullable=True)

    op.alter_column('workouts', 'name', existing_type=sa.String(), nullable=True)
    op.alter_column('workouts', 'default_sets', existing_type=sa.Integer(), nullable=True)
    op.alter_column('workouts', 'default_reps', existing_type=sa.Integer(), nullable=True)
    op.alter_column('workouts', 'default_load', existing_type=sa.Integer(), nullable=True)
