"""add case contact email and notification state"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260328_0002"
down_revision = "20260328_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.add_column("cases", sa.Column("last_notification_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("last_notification_error", sa.Text(), nullable=True))
    op.create_index("ix_cases_contact_email", "cases", ["contact_email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cases_contact_email", table_name="cases")
    op.drop_column("cases", "last_notification_error")
    op.drop_column("cases", "last_notification_sent_at")
    op.drop_column("cases", "contact_email")
