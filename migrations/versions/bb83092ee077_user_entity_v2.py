"""user entity v2

Revision ID: bb83092ee077
Revises: ca92b549616d
Create Date: 2026-04-25 16:45:43.643884

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "bb83092ee077"
down_revision: str | Sequence[str] | None = "ca92b549616d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
