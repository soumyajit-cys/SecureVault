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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

def new_func():
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MAX_LOGIN_ATTEMPTS: int = 5

    ACCOUNT_LOCK_MINUTES: int = 15

    PASSWORD_MIN_LENGTH: int = 12

    PASSWORD_REQUIRE_UPPERCASE: bool = True

    PASSWORD_REQUIRE_LOWERCASE: bool = True

    PASSWORD_REQUIRE_NUMBER: bool = True

    PASSWORD_REQUIRE_SPECIAL: bool = True

new_func()

model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

