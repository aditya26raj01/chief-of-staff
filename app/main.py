from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.auth_api import router as auth_router
from app.core.config import settings
from app.core.database.mongo import init_db
from app.core.database.postgres import engine
from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    # --- MongoDB ---
    mongo_client = await init_db()

    # --- PostgreSQL ---
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise RuntimeError("Could not connect to PostgreSQL") from e

    yield

    # --- Cleanup ---
    mongo_client.close()
    logger.info("MongoDB connection closed.")

    await engine.dispose()
    logger.info("PostgreSQL connection pool closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.include_router(auth_router)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health-check")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
