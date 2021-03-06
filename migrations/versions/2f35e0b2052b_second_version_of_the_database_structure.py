"""Second version of the database structure.

Revision ID: 2f35e0b2052b
Revises:
Create Date: 2021-10-20 10:29:45.343726

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2f35e0b2052b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "price_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.String(length=16), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(length=64), nullable=False),
        sa.Column("store", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=128), nullable=False),
        sa.Column("url", sa.String(length=256), nullable=False),
        sa.Column("price_modifier", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("product")
    op.drop_table("price_snapshot")
    # ### end Alembic commands ###
