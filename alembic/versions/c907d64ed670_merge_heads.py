"""merge heads

Revision ID: c907d64ed670
Revises: 2202f4712368, safe_not_null
Create Date: 2025-09-12 02:09:05.148264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c907d64ed670'
down_revision: Union[str, Sequence[str], None] = ('2202f4712368', 'safe_not_null')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
