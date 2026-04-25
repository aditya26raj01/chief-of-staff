import logging
from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

# In the future, import your models here and add them to this list.
# For example: from app.models.base import SampleModel
# DOCUMENT_MODELS = [SampleModel]
DOCUMENT_MODELS: list[Any] = []

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Initialize the MongoDB connection and Beanie ODM.
    """
    logger.info("Initializing MongoDB connection...")

    # Initialize Motor client
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.MONGODB_URL)

    # Initialize Beanie with the selected database and document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=DOCUMENT_MODELS,
    )

    logger.info("MongoDB connection and Beanie ODM initialized.")
