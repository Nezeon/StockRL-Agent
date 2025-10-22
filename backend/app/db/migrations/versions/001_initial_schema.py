"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

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
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('initial_budget', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_cash', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('tickers', sa.JSON(), nullable=False),
        sa.Column('allocation_strategy', sa.JSON(), nullable=True),
        sa.Column('risk_profile', sa.Enum('conservative', 'moderate', 'aggressive', name='riskprofile'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolios_id'), 'portfolios', ['id'], unique=False)
    op.create_index(op.f('ix_portfolios_user_id'), 'portfolios', ['user_id'], unique=False)

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('avg_purchase_price', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('portfolio_id', 'ticker', name='uq_portfolio_ticker')
    )
    op.create_index(op.f('ix_positions_id'), 'positions', ['id'], unique=False)
    op.create_index(op.f('ix_positions_portfolio_id'), 'positions', ['portfolio_id'], unique=False)

    # Create agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('algorithm', sa.Enum('PPO', 'DQN', 'A2C', 'SB3_PPO', 'SB3_A2C', name='agentalgorithm'), nullable=False),
        sa.Column('mode', sa.Enum('train', 'live', name='agentmode'), nullable=False),
        sa.Column('action_space_type', sa.Enum('discrete', 'continuous', name='actionspacetype'), nullable=False),
        sa.Column('hyperparameters', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('running', 'stopped', 'failed', 'completed', name='agentstatus'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_nav', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_runs_portfolio_id'), 'agent_runs', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_start_time'), 'agent_runs', ['start_time'], unique=False)

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('side', sa.Enum('BUY', 'SELL', name='tradeside'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('price', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('slippage', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0'),
        sa.Column('fees', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('simulated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trades_id'), 'trades', ['id'], unique=False)
    op.create_index(op.f('ix_trades_portfolio_id'), 'trades', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_trades_executed_at'), 'trades', ['executed_at'], unique=False)
    op.create_index(op.f('ix_trades_agent_run_id'), 'trades', ['agent_run_id'], unique=False)

    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False),
        sa.Column('episode_reward', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('cumulative_reward', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('loss', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('portfolio_nav', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('rolling_sharpe', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_metrics_id'), 'agent_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_agent_metrics_agent_run_id'), 'agent_metrics', ['agent_run_id'], unique=False)
    op.create_index('ix_agent_metrics_run_timestamp', 'agent_metrics', ['agent_run_id', 'timestamp'], unique=False)
    op.create_index('ix_agent_metrics_run_step', 'agent_metrics', ['agent_run_id', 'step'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_metrics')
    op.drop_table('trades')
    op.drop_table('agent_runs')
    op.drop_table('positions')
    op.drop_table('portfolios')
    op.drop_table('users')
