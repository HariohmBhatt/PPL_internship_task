"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2025-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index('idx_user_username_email', 'users', ['username', 'email'], unique=False)

    # Create quizzes table
    op.create_table('quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('grade_level', sa.String(length=50), nullable=False),
        sa.Column('num_questions', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('adaptive', sa.Boolean(), nullable=False, default=False),
        sa.Column('topics', sa.JSON(), nullable=False),
        sa.Column('question_types', sa.JSON(), nullable=False),
        sa.Column('standard', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quizzes_id'), 'quizzes', ['id'], unique=False)
    op.create_index(op.f('ix_quizzes_subject'), 'quizzes', ['subject'], unique=False)
    op.create_index(op.f('ix_quizzes_grade_level'), 'quizzes', ['grade_level'], unique=False)
    op.create_index('idx_quiz_subject_grade', 'quizzes', ['subject', 'grade_level'], unique=False)
    op.create_index('idx_quiz_creator_created', 'quizzes', ['creator_id', 'created_at'], unique=False)
    op.create_index('idx_quiz_difficulty', 'quizzes', ['difficulty'], unique=False)
    op.create_index('idx_quiz_published', 'quizzes', ['is_published'], unique=False)

    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, default=1),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('hint_text', sa.Text(), nullable=True),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index(op.f('ix_questions_topic'), 'questions', ['topic'], unique=False)
    op.create_index('idx_question_quiz_order', 'questions', ['quiz_id', 'order'], unique=False)
    op.create_index('idx_question_type', 'questions', ['question_type'], unique=False)
    op.create_index('idx_question_difficulty', 'questions', ['difficulty'], unique=False)

    # Create submissions table
    op.create_table('submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('max_possible_score', sa.Float(), nullable=True),
        sa.Column('percentage', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('time_taken_minutes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_submissions_id'), 'submissions', ['id'], unique=False)
    op.create_index('idx_submission_user_quiz', 'submissions', ['user_id', 'quiz_id'], unique=False)
    op.create_index('idx_submission_completed', 'submissions', ['is_completed'], unique=False)
    op.create_index('idx_submission_submitted_at', 'submissions', ['submitted_at'], unique=False)
    op.create_index('idx_submission_user_submitted', 'submissions', ['user_id', 'submitted_at'], unique=False)

    # Create answers table
    op.create_table('answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('selected_option', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=True),
        sa.Column('max_points', sa.Float(), nullable=True),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('hints_used', sa.Integer(), nullable=False, default=0),
        sa.Column('hint_penalty', sa.Float(), nullable=True, default=0.0),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_id'), 'answers', ['id'], unique=False)
    op.create_index('idx_answer_submission_question', 'answers', ['submission_id', 'question_id'], unique=False)
    op.create_index('idx_answer_question', 'answers', ['question_id'], unique=False)
    op.create_index('idx_answer_is_correct', 'answers', ['is_correct'], unique=False)

    # Create evaluations table
    op.create_table('evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('max_possible_score', sa.Float(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('correct_answers', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('mcq_score', sa.Float(), nullable=True),
        sa.Column('tf_score', sa.Float(), nullable=True),
        sa.Column('short_answer_score', sa.Float(), nullable=True),
        sa.Column('essay_score', sa.Float(), nullable=True),
        sa.Column('easy_score', sa.Float(), nullable=True),
        sa.Column('medium_score', sa.Float(), nullable=True),
        sa.Column('hard_score', sa.Float(), nullable=True),
        sa.Column('topic_scores', sa.JSON(), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=False, default=[]),
        sa.Column('weaknesses', sa.JSON(), nullable=False, default=[]),
        sa.Column('suggestions', sa.JSON(), nullable=False, default=[]),
        sa.Column('overall_feedback', sa.Text(), nullable=True),
        sa.Column('improvement_areas', sa.Text(), nullable=True),
        sa.Column('performance_level', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)
    op.create_index('idx_evaluation_submission', 'evaluations', ['submission_id'], unique=False)
    op.create_index('idx_evaluation_percentage', 'evaluations', ['percentage'], unique=False)
    op.create_index('idx_evaluation_performance_level', 'evaluations', ['performance_level'], unique=False)

    # Create retries table
    op.create_table('retries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('original_quiz_id', sa.Integer(), nullable=False),
        sa.Column('retried_quiz_id', sa.Integer(), nullable=False),
        sa.Column('retry_number', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['original_quiz_id'], ['quizzes.id'], ),
        sa.ForeignKeyConstraint(['retried_quiz_id'], ['quizzes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retries_id'), 'retries', ['id'], unique=False)
    op.create_index('idx_retry_original_quiz', 'retries', ['original_quiz_id'], unique=False)
    op.create_index('idx_retry_retried_quiz', 'retries', ['retried_quiz_id'], unique=False)
    op.create_index('idx_retry_number', 'retries', ['retry_number'], unique=False)


def downgrade() -> None:
    op.drop_table('retries')
    op.drop_table('evaluations')
    op.drop_table('answers')
    op.drop_table('submissions')
    op.drop_table('questions')
    op.drop_table('quizzes')
    op.drop_table('users')
