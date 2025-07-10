"""Merge migration heads

Revision ID: 2cdecf79399c
Revises: 001_add_pnsb_fields, 62eb23985fbe
Create Date: 2025-07-04 16:39:59.691270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cdecf79399c'
down_revision = ('001_add_pnsb_fields', '62eb23985fbe')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
