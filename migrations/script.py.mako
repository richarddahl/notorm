"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Optional
from alembic import op
import sqlalchemy as sa
import uno.database.engine  # noqa: F401
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema to this revision."""
    # First set role to admin for proper privileges
    from uno.settings import uno_settings
    from sqlalchemy import text
    admin_role = f"{uno_settings.DB_NAME}_admin"
    op.execute(text(f"SET ROLE {admin_role};"))
    
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema from this revision."""
    # First set role to admin for proper privileges
    from uno.settings import uno_settings
    from sqlalchemy import text
    admin_role = f"{uno_settings.DB_NAME}_admin"
    op.execute(text(f"SET ROLE {admin_role};"))
    
    ${downgrades if downgrades else "pass"}