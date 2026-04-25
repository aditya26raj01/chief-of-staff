"""added refresh token

Revision ID: 9da4e2338595
Revises: b0d91992ac6f
Create Date: 2026-04-25 17:13:28.271727

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9da4e2338595"
down_revision: str | Sequence[str] | None = "b0d91992ac6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
