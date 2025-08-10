"""Add leaderboard entries table.

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add leaderboard entries table."""
    op.create_table(
        'leaderboard_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('grade_level', sa.String(length=10), nullable=False),
        sa.Column('best_score', sa.Float(), nullable=False),
        sa.Column('best_percentage', sa.Float(), nullable=False),
        sa.Column('total_quizzes', sa.Integer(), nullable=False),
        sa.Column('average_score', sa.Float(), nullable=False),
        sa.Column('total_questions_answered', sa.Integer(), nullable=False),
        sa.Column('total_correct_answers', sa.Integer(), nullable=False),
        sa.Column('first_quiz_date', sa.DateTime(), nullable=False),
        sa.Column('last_quiz_date', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_leaderboard_entries_user_id'), 'leaderboard_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_leaderboard_entries_subject'), 'leaderboard_entries', ['subject'], unique=False)
    op.create_index(op.f('ix_leaderboard_entries_grade_level'), 'leaderboard_entries', ['grade_level'], unique=False)
    op.create_index(op.f('ix_leaderboard_entries_best_percentage'), 'leaderboard_entries', ['best_percentage'], unique=False)
    op.create_index(op.f('ix_leaderboard_entries_subject_grade'), 'leaderboard_entries', ['subject', 'grade_level'], unique=False)
    
    # Create unique constraint for user-subject-grade combination
    op.create_index(
        'ix_leaderboard_entries_user_subject_grade',
        'leaderboard_entries',
        ['user_id', 'subject', 'grade_level'],
        unique=True
    )


def downgrade() -> None:
    """Remove leaderboard entries table."""
    op.drop_index(op.f('ix_leaderboard_entries_user_subject_grade'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_subject_grade'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_best_percentage'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_grade_level'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_subject'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_user_id'), table_name='leaderboard_entries')
    op.drop_table('leaderboard_entries')
