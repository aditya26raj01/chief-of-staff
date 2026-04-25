from datetime import datetime

from beanie import Document
from pydantic import Field


class TimestampedDocument(Document):
    """
    An abstract base document model that automatically records
    creation and modification times.
    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Note: We aren't setting a Collection config here because this is abstract.
    # Inherit from this for actual collections, e.g.:
    # class User(TimestampedDocument):
    #     username: str
    #     class Settings:
    #         name = "users"
