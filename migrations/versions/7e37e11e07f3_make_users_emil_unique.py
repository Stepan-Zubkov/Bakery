"""Make users emil unique

Revision ID: 7e37e11e07f3
Revises: 01dfa9f9c3e2
Create Date: 2022-04-09 14:55:59.639113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e37e11e07f3'
down_revision = '01dfa9f9c3e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq_users_email'), 'users', ['email'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_users_email'), 'users', type_='unique')
    # ### end Alembic commands ###
