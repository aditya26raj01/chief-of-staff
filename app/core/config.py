from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Backend"
    API_V1_STR: str = "/api/v1"

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000"]'
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    # MongoDB Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "chief_of_staff_db"

    # PostgreSQL Settings
    POSTGRES_URL: str = "postgresql://postgres:password@localhost:5432/chief_of_staff_pg"
    POSTGRES_DB_NAME: str = "chief_of_staff_pg"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Build an asyncpg-compatible connection string.

        asyncpg doesn't understand libpq query params like `sslmode` and
        `channel_binding`, so we strip them from the URL. SSL is handled
        separately via connect_args in postgres.py.
        """
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        url = self.POSTGRES_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        parsed = urlparse(url)

        # If the URL has no explicit database path, use POSTGRES_DB_NAME.
        db_name = self.POSTGRES_DB_NAME.strip().strip("/")
        if (not parsed.path or parsed.path == "/") and db_name:
            parsed = parsed._replace(path=f"/{db_name}")

        params = parse_qs(parsed.query)
        # Remove params that asyncpg doesn't accept as URL query params
        params.pop("sslmode", None)
        params.pop("channel_binding", None)
        clean_query = urlencode(params, doseq=True)
        cleaned = parsed._replace(query=clean_query)
        return urlunparse(cleaned)

    @property
    def POSTGRES_REQUIRES_SSL(self) -> bool:
        """Check if the original URL requested SSL."""
        return "sslmode=" in self.POSTGRES_URL

    # App environment
    ENVIRONMENT: str = "dev"

    # Secrets
    SECRET_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
