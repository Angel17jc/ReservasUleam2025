"""Initial schema for payment service - Pilar 2

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-15 10:00:00.000000

Tables created:
- payment_provider_config: Configuration for payment providers
- payment: Payment transactions
- partner: External B2B partners
- partner_webhook_log: Webhook communication audit log
- webhook_event: Normalized webhook events
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # ===== payment_provider_config =====
    op.create_table(
        'payment_provider_config',
        sa.Column('id', sa.Integer(), nullable=False, comment='Internal config ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Provider identifier: stripe, mercadopago, mock'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='Provider active status'),
        sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Provider-specific configuration (API keys, webhook secrets, etc.)'),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Configuration creation timestamp (UTC)'),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp (UTC)'),
        sa.CheckConstraint("name IN ('stripe', 'mercadopago', 'mock')", name='chk_provider_name_valid'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='Payment provider configurations'
    )
    op.create_index('ix_payment_provider_config_id', 'payment_provider_config', ['id'], unique=False)
    op.create_index('ix_provider_name_active', 'payment_provider_config', ['name', 'is_active'], unique=False)
    
    # ===== payment =====
    op.create_table(
        'payment',
        sa.Column('id', sa.Integer(), nullable=False, comment='Internal payment ID'),
        sa.Column('external_payment_id', sa.String(length=255), nullable=False, comment='Unique ID from payment provider (Stripe, MercadoPago, Mock)'),
        sa.Column('reserva_id', sa.Integer(), nullable=False, comment='FK to rest-service.reserva.id'),
        sa.Column('usuario_id', sa.Integer(), nullable=False, comment='FK to rest-service.usuario.id'),
        sa.Column('provider_name', sa.String(length=50), nullable=False, comment='Payment provider: stripe, mercadopago, mock'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Payment amount (positive decimal)'),
        sa.Column('currency', sa.String(length=3), nullable=False, comment='ISO 4217 currency code (USD, EUR, MXN, etc.)'),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'CANCELLED', name='paymentstatus'), nullable=False, comment='Current payment status'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Additional payment metadata (client_secret, checkout_url, etc.)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if payment failed'),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Creation timestamp (UTC)'),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp (UTC)'),
        sa.CheckConstraint('amount > 0', name='chk_payment_amount_positive'),
        sa.CheckConstraint('length(currency) = 3', name='chk_payment_currency_length'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_payment_id'),
        comment='Payment transactions with provider integration'
    )
    op.create_index('ix_payment_external_payment_id', 'payment', ['external_payment_id'], unique=True)
    op.create_index('ix_payment_id', 'payment', ['id'], unique=False)
    op.create_index('ix_payment_provider_name', 'payment', ['provider_name'], unique=False)
    op.create_index('ix_payment_reserva_id', 'payment', ['reserva_id'], unique=False)
    op.create_index('ix_payment_status', 'payment', ['status'], unique=False)
    op.create_index('ix_payment_usuario_id', 'payment', ['usuario_id'], unique=False)
    op.create_index('ix_payment_reserva_usuario', 'payment', ['reserva_id', 'usuario_id'], unique=False)
    op.create_index('ix_payment_status_created', 'payment', ['status', 'creado_en'], unique=False)
    
    # ===== partner =====
    op.create_table(
        'partner',
        sa.Column('id', sa.Integer(), nullable=False, comment='Internal partner ID'),
        sa.Column('nombre', sa.String(length=200), nullable=False, comment='Partner name (must be unique)'),
        sa.Column('descripcion', sa.Text(), nullable=True, comment='Partner description or notes'),
        sa.Column('webhook_url', sa.String(length=500), nullable=False, comment="Partner's webhook endpoint URL (HTTPS recommended)"),
        sa.Column('shared_secret', sa.String(length=128), nullable=False, comment='HMAC-SHA256 secret for webhook signature validation'),
        sa.Column('eventos_suscritos', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment="Array of event types: ['booking.confirmed', 'payment.success']"),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment="Partner active status (inactive partners don't receive webhooks)"),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Partner registration timestamp (UTC)'),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp (UTC)'),
        sa.CheckConstraint('length(shared_secret) >= 32', name='chk_partner_secret_length'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        comment='External partners for B2B webhook integrations'
    )
    op.create_index('ix_partner_id', 'partner', ['id'], unique=False)
    op.create_index('ix_partner_is_active', 'partner', ['is_active'], unique=False)
    op.create_index('ix_partner_active_created', 'partner', ['is_active', 'creado_en'], unique=False)
    
    # ===== partner_webhook_log =====
    op.create_table(
        'partner_webhook_log',
        sa.Column('id', sa.Integer(), nullable=False, comment='Log entry ID'),
        sa.Column('partner_id', sa.Integer(), nullable=False, comment='FK to partner.id'),
        sa.Column('event_type', sa.String(length=100), nullable=False, comment='Event type (booking.confirmed, payment.success, etc.)'),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Complete webhook payload'),
        sa.Column('response_status', sa.Integer(), nullable=True, comment='HTTP status code from partner (200, 404, 500, etc.)'),
        sa.Column('response_body', sa.Text(), nullable=True, comment='Response body from partner'),
        sa.Column('signature_valid', sa.Boolean(), nullable=True, comment='HMAC signature validation result (for incoming webhooks)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if webhook delivery failed'),
        sa.Column('direction', sa.String(length=10), nullable=False, comment="Webhook direction: 'outgoing' (sent to partner) or 'incoming' (received from partner)"),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Log entry timestamp (UTC)'),
        sa.CheckConstraint("direction IN ('outgoing', 'incoming')", name='chk_webhook_direction'),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit log for partner webhook communications'
    )
    op.create_index('ix_partner_webhook_log_event_type', 'partner_webhook_log', ['event_type'], unique=False)
    op.create_index('ix_partner_webhook_log_id', 'partner_webhook_log', ['id'], unique=False)
    op.create_index('ix_partner_webhook_log_partner_id', 'partner_webhook_log', ['partner_id'], unique=False)
    op.create_index('ix_webhook_log_event_status', 'partner_webhook_log', ['event_type', 'response_status'], unique=False)
    op.create_index('ix_webhook_log_partner_created', 'partner_webhook_log', ['partner_id', 'creado_en'], unique=False)
    
    # ===== webhook_event =====
    op.create_table(
        'webhook_event',
        sa.Column('id', sa.Integer(), nullable=False, comment='Internal event ID'),
        sa.Column('event_type', sa.String(length=100), nullable=False, comment='Normalized event type: payment.success, payment.failed, booking.confirmed, etc.'),
        sa.Column('source', sa.String(length=50), nullable=False, comment='Event source: stripe, mercadopago, mock, partner:{partner_id}'),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Normalized event payload with all relevant data'),
        sa.Column('processed', sa.Boolean(), nullable=True, comment='Processing status (True = successfully processed)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if processing failed'),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Event receipt timestamp (UTC)'),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last processing attempt timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        comment='Normalized webhook events from all sources'
    )
    op.create_index('ix_webhook_event_event_type', 'webhook_event', ['event_type'], unique=False)
    op.create_index('ix_webhook_event_id', 'webhook_event', ['id'], unique=False)
    op.create_index('ix_webhook_event_processed', 'webhook_event', ['processed'], unique=False)
    op.create_index('ix_webhook_event_source', 'webhook_event', ['source'], unique=False)
    op.create_index('ix_webhook_event_processed_created', 'webhook_event', ['processed', 'creado_en'], unique=False)
    op.create_index('ix_webhook_event_source_created', 'webhook_event', ['source', 'creado_en'], unique=False)
    op.create_index('ix_webhook_event_type_processed', 'webhook_event', ['event_type', 'processed'], unique=False)


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop tables in reverse order
    op.drop_table('webhook_event')
    op.drop_table('partner_webhook_log')
    op.drop_table('partner')
    op.drop_table('payment')
    op.drop_table('payment_provider_config')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS paymentstatus')
