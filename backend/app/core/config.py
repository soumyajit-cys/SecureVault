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
    JWT_ALGORITHM: str = "RS256"
    JWT_KEY_ROTATION_DAYS: int = 90
    JWT_RETIRED_KEY_GRACE_DAYS: int = 14
    JWT_LEEWAY_SECONDS: int = 10

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MFA_TOKEN_EXPIRE_MINUTES: int = 5
    TOTP_ISSUER: str = "SecureVault"
    TOTP_PERIOD_SECONDS: int = 30
    TOTP_DIGITS: int = 6
    TOTP_WINDOW: int = 1
    MFA_RECOVERY_CODE_COUNT: int = 10

    EMAIL_VERIFICATION_REQUIRED: bool = False
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    EMAIL_BACKEND: str = "console"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True
    APP_BASE_URL: str = "http://localhost:5173"

    PWNED_CHECK_ENABLED: bool = False
    PWNED_ON_BREACH: str = "block"
    PWNED_TIMEOUT_SECONDS: int = 3

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
    RATE_LIMIT_BACKEND: str = "local"
    REDIS_URL: str | None = None

    TRUSTED_PROXY_COUNT: int = 1

    ENABLE_METRICS: bool = True
    ENABLE_SECURITY_HEADERS: bool = True

    KMS_BACKEND: str = "local"
    KMS_TRANSIT_URL: str | None = None
    KMS_TRANSIT_TOKEN: str | None = None
    KMS_TRANSIT_KEY: str | None = None
    KMS_TRANSIT_TIMEOUT_SECONDS: int = 5

    DATA_RETENTION_DAYS: int = 90
    ENABLE_RIGHT_TO_ERASURE: bool = True

    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
