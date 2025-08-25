"""set_email_fields_not_null

Revision ID: ff6e74a1534c
Revises: c436afb1c42b
Create Date: 2025-08-24 17:42:13.904302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff6e74a1534c'
down_revision: Union[str, Sequence[str], None] = 'c436afb1c42b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', nullable=False)
        batch_op.alter_column('is_email_verified', nullable=False)

    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('user_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', nullable=True)
        batch_op.alter_column('is_email_verified', nullable=True)

    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('user_id', nullable=True)
