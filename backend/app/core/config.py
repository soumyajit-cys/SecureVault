from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SecureVault"
    APP_ENV: str = "development"

    API_V1_PREFIX: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_MINUTES: int = 15

    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBER: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    VAULT_ADMIN_EMAIL: str | None = None
    VAULT_ADMIN_USERNAME: str | None = None
    VAULT_ADMIN_PASSWORD: str | None = None

    STORAGE_DIR: str = "storage"

    ENCRYPTED_FILE_EXTENSION: str = ".svlt"
    ENCRYPTED_ARCHIVE_EXTENSION: str = ".svltz"

    KEY_ROTATION_INTERVAL_DAYS: int = 90
    KEY_RETENTION_DAYS: int = 365

    GARBAGE_COLLECTION_ENABLED: bool = True
    GARBAGE_COLLECTION_INTERVAL_HOURS: int = 24
    TEMP_FILE_MAX_AGE_HOURS: int = 24

    MAX_UPLOAD_SIZE_BYTES: int = 4 * 1024 * 1024 * 1024

    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    CORS_ALLOW_CREDENTIALS: bool = True

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10

    TRUSTED_PROXY_COUNT: int = 1

    ENABLE_METRICS: bool = True
    ENABLE_SECURITY_HEADERS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
