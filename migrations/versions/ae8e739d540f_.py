"""empty message

Revision ID: ae8e739d540f
Revises:
Create Date: 2024-05-14 10:51:56.598992

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae8e739d540f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("timetable", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "course_position",
                sa.Integer(),
                server_default=sa.text("'1'"),
                nullable=False,
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("timetable", schema=None) as batch_op:
        batch_op.drop_column("course_position")

    # ### end Alembic commands ###
