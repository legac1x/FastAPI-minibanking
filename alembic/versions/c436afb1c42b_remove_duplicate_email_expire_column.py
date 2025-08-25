"""remove_duplicate_email_expire_column

Revision ID: c436afb1c42b
Revises: 830bdd5b95ae
Create Date: 2025-08-24 17:38:29.086024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c436afb1c42b'
down_revision: Union[str, Sequence[str], None] = '830bdd5b95ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('emila_veritied_code_expire')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('emila_veritied_code_expire', sa.DateTime(), nullable=True))
