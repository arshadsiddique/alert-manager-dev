"""Initial complete schema with JSM and enhanced matching fields

Revision ID: 0001
Revises: 
Create Date: 2025-06-27 11:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('alert_id', sa.String(), nullable=True),
        sa.Column('alert_name', sa.String(), nullable=True),
        sa.Column('cluster', sa.String(), nullable=True),
        sa.Column('pod', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('generator_url', sa.String(), nullable=True),
        sa.Column('grafana_status', sa.String(), nullable=True, server_default='active'),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('annotations', sa.JSON(), nullable=True),

        # Legacy Jira integration
        sa.Column('jira_status', sa.String(), nullable=True, server_default='open'),
        sa.Column('jira_issue_key', sa.String(), nullable=True),
        sa.Column('jira_issue_id', sa.String(), nullable=True),
        sa.Column('jira_issue_url', sa.String(), nullable=True),
        sa.Column('jira_assignee', sa.String(), nullable=True),
        sa.Column('jira_assignee_email', sa.String(), nullable=True),

        # Acknowledgement / Resolution tracking
        sa.Column('acknowledged_by', sa.String(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),

        # JSM Integration
        sa.Column('jsm_alert_id', sa.String(), nullable=True),
        sa.Column('jsm_tiny_id', sa.String(), nullable=True),
        sa.Column('jsm_status', sa.String(), nullable=True),
        sa.Column('jsm_acknowledged', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('jsm_owner', sa.String(), nullable=True),
        sa.Column('jsm_priority', sa.String(), nullable=True),
        sa.Column('jsm_alias', sa.String(), nullable=True),
        sa.Column('jsm_integration_name', sa.String(), nullable=True),
        sa.Column('jsm_source', sa.String(), nullable=True),
        sa.Column('jsm_count', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('jsm_tags', sa.JSON(), nullable=True),
        sa.Column('jsm_last_occurred_at', sa.DateTime(), nullable=True),
        sa.Column('jsm_created_at', sa.DateTime(), nullable=True),
        sa.Column('jsm_updated_at', sa.DateTime(), nullable=True),

        # Alert matching fields
        sa.Column('match_type', sa.String(), nullable=True),
        sa.Column('match_confidence', sa.Float(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('match_details', sa.JSON(), nullable=True),
        sa.Column('manual_review_required', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('matching_timestamp', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Add indexes
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_alert_id', 'alerts', ['alert_id'], unique=True)
    op.create_index('ix_alerts_alert_name', 'alerts', ['alert_name'])
    op.create_index('ix_alerts_cluster', 'alerts', ['cluster'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_grafana_status', 'alerts', ['grafana_status'])
    op.create_index('ix_alerts_jira_status', 'alerts', ['jira_status'])
    op.create_index('ix_alerts_jsm_alert_id', 'alerts', ['jsm_alert_id'])
    op.create_index('ix_alerts_jsm_tiny_id', 'alerts', ['jsm_tiny_id'])
    op.create_index('ix_alerts_jsm_status', 'alerts', ['jsm_status'])
    op.create_index('ix_alerts_jsm_acknowledged', 'alerts', ['jsm_acknowledged'])
    op.create_index('ix_alerts_match_type', 'alerts', ['match_type'])
    op.create_index('ix_alerts_match_score', 'alerts', ['match_score'])
    op.create_index('ix_alerts_manual_review_required', 'alerts', ['manual_review_required'])

    # Create cron_config table
    op.create_table(
        'cron_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_name', sa.String(), nullable=True),
        sa.Column('cron_expression', sa.String(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('job_name')
    )

    # Insert default cron jobs
    op.execute("""
        INSERT INTO cron_config (job_name, cron_expression, is_enabled, created_at, updated_at)
        VALUES 
            ('grafana-sync', '*/10 * * * *', true, NOW(), NOW()),
            ('jsm-sync', '*/5 * * * *', true, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_table('cron_config')

    index_names = [
        'ix_alerts_id',
        'ix_alerts_alert_id',
        'ix_alerts_alert_name',
        'ix_alerts_cluster',
        'ix_alerts_severity',
        'ix_alerts_grafana_status',
        'ix_alerts_jira_status',
        'ix_alerts_jsm_alert_id',
        'ix_alerts_jsm_tiny_id',
        'ix_alerts_jsm_status',
        'ix_alerts_jsm_acknowledged',
        'ix_alerts_match_type',
        'ix_alerts_match_score',
        'ix_alerts_manual_review_required'
    ]
    for index in index_names:
        op.drop_index(index, table_name='alerts')

    op.drop_table('alerts')