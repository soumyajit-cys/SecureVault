import pytest

from fastapi.testclient import TestClient

from app.core.config import get_settings

from app.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: (
            get_settings()
            .model_copy(
                update={
                    "EMAIL_VERIFICATION_REQUIRED": True,
                }
            )
        ),
    )

    monkeypatch.setattr(
        "app.services.auth.auth_service.settings",
        get_settings().model_copy(
            update={
                "EMAIL_VERIFICATION_REQUIRED": True,
            }
        ),
    )

    monkeypatch.setattr(
        "app.services.auth.email_verification_service.settings",
        get_settings().model_copy(
            update={
                "EMAIL_VERIFICATION_REQUIRED": True,
            }
        ),
    )

    app = create_app()

    with TestClient(app) as c:
        yield c


def test_register_requires_verification(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert response.status_code == 200


def test_login_requires_verified_email(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify2@example.com",
            "username": "verifyuser2",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "verify2@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert response.status_code == 403
    assert "verified" in response.json()["detail"]
