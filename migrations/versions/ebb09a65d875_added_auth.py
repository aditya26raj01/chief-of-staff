"""added auth

Revision ID: ebb09a65d875
Revises: 9da4e2338595
Create Date: 2026-04-25 17:32:20.514531

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ebb09a65d875"
down_revision: str | Sequence[str] | None = "9da4e2338595"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
