from __future__ import annotations

import pytest

from app.core import security
from app.core.config import settings


@pytest.fixture
def admin_creds(monkeypatch):
    """Configure runtime admin credentials with a known password."""
    password = "test-pass-1234"
    pwd_hash = security.hash_password(password)
    monkeypatch.setattr(settings, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", pwd_hash)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-secret-key-not-for-production-use")
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    return {"username": "admin", "password": password}


def test_login_success(client_no_auth_override, admin_creds):
    resp = client_no_auth_override.post(
        "/api/v1/auth/login",
        json={"username": admin_creds["username"], "password": admin_creds["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20
    assert body["expires_in"] == 30 * 60


def test_login_wrong_password(client_no_auth_override, admin_creds):
    resp = client_no_auth_override.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_credentials"


def test_login_unknown_user(client_no_auth_override, admin_creds):
    resp = client_no_auth_override.post(
        "/api/v1/auth/login",
        json={"username": "ghost", "password": admin_creds["password"]},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_credentials"


def test_login_when_unconfigured(client_no_auth_override, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", "")
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "")
    resp = client_no_auth_override.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "anything"},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "auth_not_configured"


def test_me_with_valid_token(client_no_auth_override, admin_creds):
    login = client_no_auth_override.post(
        "/api/v1/auth/login",
        json=admin_creds,
    )
    token = login.json()["access_token"]
    resp = client_no_auth_override.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"username": "admin"}


def test_me_without_token(client_no_auth_override, admin_creds):
    resp = client_no_auth_override.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "not_authenticated"


def test_me_with_invalid_token(client_no_auth_override, admin_creds):
    resp = client_no_auth_override.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_token"


def test_protected_route_blocks_anon(client_no_auth_override, admin_creds):
    """业务路由（/customers）在没有 override 时应该被守卫挡住。"""
    resp = client_no_auth_override.get("/api/v1/customers")
    assert resp.status_code == 401


def test_protected_route_allows_with_token(client_no_auth_override, admin_creds):
    login = client_no_auth_override.post("/api/v1/auth/login", json=admin_creds)
    token = login.json()["access_token"]
    resp = client_no_auth_override.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
