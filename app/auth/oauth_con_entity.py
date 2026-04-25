import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.pg_base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.auth.user_entity import User


class OAuthProvider(enum.StrEnum):
    GOOGLE = "google"


class OAuthConnection(TimestampMixin, Base):
    __tablename__ = "oauth_connections"
    __table_args__ = (
        UniqueConstraint("provider", "providerAccountId", name="uq_oauth_provider_account"),
        UniqueConstraint("userId", "provider", name="uq_oauth_user_provider"),
        Index("ix_oauth_connections_provider_account_id", "providerAccountId"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        "userId",
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="oauth_connections")

    provider: Mapped[OAuthProvider] = mapped_column(
        Enum(
            OAuthProvider,
            name="oauth_provider",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    provider_account_id: Mapped[str] = mapped_column(
        "providerAccountId", String(128), nullable=False
    )
    provider_email: Mapped[str] = mapped_column("providerEmail", String(320), nullable=False)

    access_token_encrypted: Mapped[str | None] = mapped_column(
        "accessTokenEncrypted", nullable=True
    )
    refresh_token_encrypted: Mapped[str | None] = mapped_column(
        "refreshTokenEncrypted", nullable=True
    )
    access_token_expires_at: Mapped[datetime | None] = mapped_column(
        "accessTokenExpiresAt",
        DateTime(timezone=True),
        nullable=True,
    )
    scope: Mapped[str | None] = mapped_column(nullable=True)
    token_type: Mapped[str | None] = mapped_column("tokenType", String(32), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        "revokedAt", DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        "createdAt",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
