"""Update from_account_id field

Revision ID: 0e2b0ea8cb87
Revises: 5e4937cfa9fd
Create Date: 2025-08-04 15:36:49.508463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e2b0ea8cb87'
down_revision: Union[str, Sequence[str], None] = '5e4937cfa9fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('from_account_id',
               existing_type=sa.INTEGER(),
               nullable=True)

def downgrade():
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('from_account_id',
               existing_type=sa.INTEGER(),
               nullable=False)
