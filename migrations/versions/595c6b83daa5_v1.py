"""v1

Revision ID: 595c6b83daa5
Revises: 
Create Date: 2023-11-25 16:03:24.269652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '595c6b83daa5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('linear_accelerator',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('characteristics', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('patient',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('organ_type', sa.String(length=50), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('number_of_fractions', sa.Integer(), nullable=False),
    sa.Column('patient_type', sa.String(length=20), nullable=False),
    sa.Column('treatment_duration', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('appointment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('linear_accelerator_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['linear_accelerator_id'], ['linear_accelerator.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('test')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('test',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('appointment')
    op.drop_table('patient')
    op.drop_table('linear_accelerator')
    # ### end Alembic commands ###