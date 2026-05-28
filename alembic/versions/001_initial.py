"""사주담 초기 테이블 생성

Revision ID: 001
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('oauth_provider', sa.String(20), nullable=False),  # kakao | google
        sa.Column('oauth_id', sa.String(100), nullable=False),
        sa.Column('nickname', sa.String(50), nullable=True),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('birth_month', sa.Integer(), nullable=True),
        sa.Column('birth_day', sa.Integer(), nullable=True),
        sa.Column('birth_hour', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(10), default='female'),
        sa.Column('lang', sa.String(5), default='ko'),
        sa.Column('disclaimer_accepted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('oauth_provider', 'oauth_id', name='uq_oauth'),
    )

    op.create_table('insight_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('saju_data', sa.Text(), nullable=True),   # JSON
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('lang', sa.String(5), default='ko'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('insight_sessions')
    op.drop_table('users')
