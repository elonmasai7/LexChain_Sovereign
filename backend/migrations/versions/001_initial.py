"""Initial database schema migration."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='client'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('webauthn_credential_id', sa.String(512), nullable=True),
        sa.Column('webauthn_public_key', sa.Text(), nullable=True),
        sa.Column('wallet_address', sa.String(255), nullable=True),
        sa.Column('did', sa.String(255), nullable=True, unique=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_wallet', 'users', ['wallet_address'], unique=False, postgresql_where=sa.text('wallet_address IS NOT NULL'))

    # Sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('device_fingerprint', sa.String(512), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_sessions_token_hash', 'user_sessions', ['token_hash'])

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])

    # Assets table
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('token_id', sa.String(255), nullable=True),
        sa.Column('contract_address', sa.String(255), nullable=True),
        sa.Column('chain_id', sa.Integer(), nullable=True),
        sa.Column('total_supply', sa.Numeric(precision=78, decimal_places=0), nullable=True),
        sa.Column('circulating_supply', sa.Numeric(precision=78, decimal_places=0), server_default='0'),
        sa.Column('fractional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('legal_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('compliance_rules', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('verification_status', sa.String(50), nullable=False, server_default='unverified'),
        sa.Column('custodian', sa.String(255), nullable=True),
        sa.Column('valuation', sa.Numeric(precision=20, decimal_places=2), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_assets_type_status', 'assets', ['asset_type', 'status'])
    op.create_index('idx_assets_chain', 'assets', ['chain_id', 'contract_address'])

    # Additional tables would be created here...


def downgrade() -> None:
    op.drop_table('assets')
    op.drop_table('audit_logs')
    op.drop_table('user_sessions')
    op.drop_table('users')