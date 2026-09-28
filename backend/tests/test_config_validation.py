import pytest

import app.core.security_settings as sec
from app.core.security_settings import (
    validate_cors_settings,
    validate_database_settings,
    validate_redis_settings,
    validate_security_settings,
)


@pytest.fixture
def prod(monkeypatch):
    monkeypatch.setattr(sec.settings, "APP_ENV", "production")
    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setattr(
        sec.settings, "REDIS_URL", "rediss://default:pass@host:6379"
    )
    yield sec.settings


def test_database_rejects_bare_postgresql_scheme(monkeypatch):
    monkeypatch.setattr(
        sec.settings,
        "DATABASE_URL",
        "postgresql://user:[REDACTED]@host:5432/db",
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_database_settings()
    assert "postgresql+psycopg://" in str(exc_info.value)


def test_database_rejects_unknown_scheme(monkeypatch):
    monkeypatch.setattr(
        sec.settings, "DATABASE_URL", "mysql://host/db"
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_database_settings()
    assert "mysql" in str(exc_info.value)


def test_database_rejects_channel_binding_require(monkeypatch):
    monkeypatch.setattr(
        sec.settings,
        "DATABASE_URL",
        "postgresql+psycopg://user:[REDACTED]@host:5432/db"
        "?sslmode=require&channel_binding=require",
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_database_settings()
    assert "channel_binding" in str(exc_info.value)


def test_database_accepts_psycopg_and_sqlite(monkeypatch):
    monkeypatch.setattr(
        sec.settings,
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@host:5432/db?sslmode=require",
    )
    validate_database_settings()

    monkeypatch.setattr(
        sec.settings, "DATABASE_URL", "sqlite:///:memory:"
    )
    validate_database_settings()


def test_redis_rejects_postgres_url(monkeypatch):
    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setattr(
        sec.settings,
        "REDIS_URL",
        "postgresql+psycopg://user:pass@host:5432/db",
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_redis_settings()
    assert "DATABASE_URL" in str(exc_info.value)


def test_redis_rejects_upstash_rest_url(monkeypatch):
    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setattr(
        sec.settings,
        "REDIS_URL",
        "https://example-abc123.upstash.io",
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_redis_settings()
    assert "REST" in str(exc_info.value)


def test_redis_rejects_missing_and_bad_scheme(monkeypatch):
    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "redis")

    monkeypatch.setattr(sec.settings, "REDIS_URL", None)
    with pytest.raises(RuntimeError):
        validate_redis_settings()

    monkeypatch.setattr(sec.settings, "REDIS_URL", "http://host:80")
    with pytest.raises(RuntimeError):
        validate_redis_settings()


def test_redis_accepts_redis_schemes_and_skips_local(monkeypatch):
    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "redis")

    monkeypatch.setattr(
        sec.settings, "REDIS_URL", "rediss://default:pass@host:6379"
    )
    validate_redis_settings()

    monkeypatch.setattr(
        sec.settings, "REDIS_URL", "redis://localhost:6379"
    )
    validate_redis_settings()

    monkeypatch.setattr(sec.settings, "RATE_LIMIT_BACKEND", "local")
    monkeypatch.setattr(sec.settings, "REDIS_URL", "garbage")
    validate_redis_settings()


def test_cors_rejects_unparsable_and_wildcard(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "not-json")
    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_settings()
    assert "JSON list" in str(exc_info.value)

    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS", '{"a": 1}'
    )
    with pytest.raises(RuntimeError):
        validate_cors_settings()

    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setattr(sec.settings, "CORS_ALLOW_ORIGINS", ["*"])
    monkeypatch.setattr(sec.settings, "CORS_ALLOW_CREDENTIALS", True)
    with pytest.raises(RuntimeError) as exc_info:
        validate_cors_settings()
    assert '"*"' in str(exc_info.value)


def test_cors_rejects_non_url_entry(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setattr(
        sec.settings, "CORS_ALLOW_ORIGINS", ["vault.example.com"]
    )
    with pytest.raises(RuntimeError):
        validate_cors_settings()


def test_cors_accepts_exact_origins(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS", '["https://vault.example.com"]'
    )
    monkeypatch.setattr(
        sec.settings,
        "CORS_ALLOW_ORIGINS",
        ["https://vault.example.com"],
    )
    validate_cors_settings()


def test_prod_rejects_placeholder_and_short_admin_password(prod):
    prod.SECRET_KEY = "x" * 32
    prod.VAULT_ADMIN_PASSWORD = "change-me-Str0ng!AdminPass"
    with pytest.raises(RuntimeError) as exc_info:
        validate_security_settings()
    assert "VAULT_ADMIN_PASSWORD" in str(exc_info.value)

    prod.VAULT_ADMIN_PASSWORD = "short1!"
    with pytest.raises(RuntimeError) as exc_info:
        validate_security_settings()
    assert "password" in str(exc_info.value).lower()

    prod.VAULT_ADMIN_PASSWORD = "Long-Enough-Admin-Pass-1!"
    validate_security_settings()


def test_prod_rejects_changeme_secret(prod):
    prod.SECRET_KEY = "CHANGEME-generate-32-plus-random-chars"
    prod.VAULT_ADMIN_PASSWORD = None
    with pytest.raises(RuntimeError) as exc_info:
        validate_security_settings()
    assert "SECRET_KEY" in str(exc_info.value)
