"""Add users table

Revision ID: 01dfa9f9c3e2
Revises: fe85d3474b9d
Create Date: 2022-04-09 14:42:52.282688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01dfa9f9c3e2'
down_revision = 'fe85d3474b9d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password', sa.Text(), nullable=False),
    sa.Column('access_key', sa.String(length=100), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('first_name', sa.String(length=50), nullable=False),
    sa.Column('last_name', sa.String(length=50), nullable=False),
    sa.Column('address', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.alter_column('products', 'sales',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('products', 'image_url',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('products', 'image_url',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('products', 'sales',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_table('users')
    # ### end Alembic commands ###
