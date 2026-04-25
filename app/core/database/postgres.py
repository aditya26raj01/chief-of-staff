import ssl as ssl_module
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Build connect_args for asyncpg (SSL handled here, not in URL)
connect_args: dict[str, object] = {}
if settings.POSTGRES_REQUIRES_SSL:
    ssl_ctx = ssl_module.create_default_context()
    connect_args["ssl"] = ssl_ctx

# Create the async engine
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.ENVIRONMENT == "dev",  # Log SQL queries in development
    future=True,
    pool_pre_ping=True,  # Check connection health before checking out from pool
    connect_args=connect_args,
)

# Create a configured "Session" class
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically commits if no exceptions occur, otherwise rolls back.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
