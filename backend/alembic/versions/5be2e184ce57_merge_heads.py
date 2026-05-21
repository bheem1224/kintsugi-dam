"""merge_heads

Revision ID: 5be2e184ce57
Revises: 1eb28e1c0aea, 26497acbe027, ca3af4ab3d31
Create Date: 2026-05-21 01:29:29.728625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5be2e184ce57'
down_revision: Union[str, Sequence[str], None] = ('1eb28e1c0aea', '26497acbe027', 'ca3af4ab3d31')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
