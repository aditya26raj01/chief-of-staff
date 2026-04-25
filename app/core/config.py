import base64
import binascii

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

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8080/auth/google/callback"
    GOOGLE_OAUTH_SCOPES: list[str] = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    # Auth and token settings
    JWT_SECRET: str = ""
    ACCESS_TOKEN_SECRET: str = ""
    ACCESS_TOKEN_EXPIRES_IN_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRES_IN_SECONDS: int = 2592000
    REFRESH_TOKEN_PEPPER: str = ""
    OAUTH_TOKEN_ENCRYPTION_KEY: str = ""

    @field_validator("GOOGLE_OAUTH_SCOPES", mode="before")
    @classmethod
    def assemble_google_scopes(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [scope.strip() for scope in v.split(",") if scope.strip()]
        if isinstance(v, list):
            return [scope.strip() for scope in v if scope.strip()]
        raise ValueError(v)

    @field_validator("OAUTH_TOKEN_ENCRYPTION_KEY")
    @classmethod
    def validate_oauth_encryption_key(cls, v: str) -> str:
        # Must decode to exactly 32 bytes for AES-256-GCM.
        if not v:
            return v
        try:
            raw = base64.urlsafe_b64decode(v.encode("utf-8"))
        except (binascii.Error, ValueError) as exc:
            raise ValueError("OAUTH_TOKEN_ENCRYPTION_KEY must be url-safe base64") from exc
        if len(raw) != 32:
            raise ValueError("OAUTH_TOKEN_ENCRYPTION_KEY must decode to 32 bytes")
        return v

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

    @property
    def EFFECTIVE_ACCESS_TOKEN_SECRET(self) -> str:
        return self.ACCESS_TOKEN_SECRET or self.JWT_SECRET

    # App environment
    ENVIRONMENT: str = "dev"

    # Secrets
    SECRET_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
