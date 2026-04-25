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

    try:
        # Initialize Motor client
        client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # Fail fast if DB is down
        )

        # Ping the database to verify the connection
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB.")

        # Initialize Beanie with the selected database and document models
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=DOCUMENT_MODELS,
        )

        logger.info("Beanie ODM initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Raising the exception here will cause the FastAPI application startup to fail.
        raise RuntimeError("Could not connect to MongoDB") from e
