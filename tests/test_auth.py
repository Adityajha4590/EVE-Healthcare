"""Comprehensive tests for Phase 2 — authentication and user management."""

import jwt
import pytest

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User


# ============================================================================
# Helpers
# ============================================================================


def _signup(client, email="test@example.com", password="securepassword"):
    return client.post("/auth/signup", json={"email": email, "password": password})


def _login(client, email="test@example.com", password="securepassword"):
    return client.post("/auth/login", json={"email": email, "password": password})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Signup
# ============================================================================


class TestSignup:
    """POST /auth/signup"""

    def test_signup_success(self, client):
        resp = _signup(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "is_active" in data
        assert "created_at" in data

    def test_signup_normalizes_email(self, client):
        resp = _signup(client, email="  Normalize@EXAMPLE.com  ")
        assert resp.status_code == 201
        assert resp.json()["email"] == "normalize@example.com"

    def test_signup_response_excludes_password(self, client):
        resp = _signup(client)
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_signup_stores_hash_not_plaintext(self, client, db_session):
        _signup(client, email="hash@example.com", password="myplaintextpw")
        user = db_session.query(User).filter(User.email == "hash@example.com").first()
        assert user is not None
        assert user.password_hash != "myplaintextpw"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    def test_signup_duplicate_email(self, client):
        _signup(client, email="dup@example.com")
        resp = _signup(client, email="dup@example.com")
        assert resp.status_code == 409

    def test_signup_invalid_email(self, client):
        resp = _signup(client, email="not-an-email")
        assert resp.status_code == 422

    def test_signup_password_too_short(self, client):
        resp = _signup(client, password="short")
        assert resp.status_code == 422

    def test_signup_missing_fields(self, client):
        resp = client.post("/auth/signup", json={})
        assert resp.status_code == 422

    def test_signup_password_within_byte_limit(self, client):
        """Password of 72 ASCII chars (= 72 bytes) is accepted."""
        pw = "a" * 72
        resp = _signup(client, email="bytelen72@example.com", password=pw)
        assert resp.status_code == 201

    def test_signup_password_exceeds_byte_limit(self, client):
        """Password of 73 ASCII chars (= 73 bytes) is rejected with 422."""
        pw = "a" * 73
        resp = _signup(client, email="bytelen73@example.com", password=pw)
        assert resp.status_code == 422

    def test_signup_unicode_password_exceeds_byte_limit(self, client):
        """Unicode password with <=72 chars but >72 UTF-8 bytes is rejected."""
        # 'ä' is 2 UTF-8 bytes, so 37 of them = 74 bytes > 72
        pw = "ä" * 37  # 37 chars, 74 bytes
        assert len(pw) == 37
        assert len(pw.encode("utf-8")) == 74
        resp = _signup(client, email="unicode@example.com", password=pw)
        assert resp.status_code == 422

    def test_signup_long_password_never_reaches_bcrypt(self, client, monkeypatch):
        """Verify that an over-limit password is rejected before bcrypt is called."""
        import app.core.security as sec
        original_hash = sec.hash_password

        was_called = False
        def spy(pw):
            nonlocal was_called
            was_called = True
            return original_hash(pw)

        monkeypatch.setattr(sec, "hash_password", spy)

        pw = "a" * 73
        resp = _signup(client, email="nohash@example.com", password=pw)
        assert resp.status_code == 422
        assert not was_called, "hash_password should not have been called"


# ============================================================================
# Login
# ============================================================================


class TestLogin:
    """POST /auth/login"""

    def test_login_success(self, client):
        _signup(client)
        resp = _login(client)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_token_has_expected_claims(self, client):
        _signup(client)
        resp = _login(client)
        token = resp.json()["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        # Must NOT contain password
        assert "password" not in payload
        assert "password_hash" not in payload

    def test_login_wrong_password(self, client):
        _signup(client)
        resp = _login(client, password="wrongpassword")
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = _login(client, email="nobody@example.com")
        assert resp.status_code == 401

    def test_login_error_does_not_reveal_email_vs_password(self, client):
        _signup(client)
        resp_bad_email = client.post("/auth/login", json={"email": "nobody@example.com", "password": "securepassword"})
        resp_bad_pass = client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
        # Both should return the same generic error message
        assert resp_bad_email.json()["detail"] == resp_bad_pass.json()["detail"]


# ============================================================================
# GET /auth/me — authentication & authorization
# ============================================================================


class TestAuthMe:
    """GET /auth/me"""

    def test_me_success(self, client):
        _signup(client)
        token = _login(client).json()["access_token"]
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    def test_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_malformed_token(self, client):
        resp = client.get("/auth/me", headers=_auth_header("not.a.real.token"))
        assert resp.status_code == 401

    def test_me_invalid_signature(self, client):
        _signup(client)
        token = jwt.encode({"sub": "fake-id", "exp": 9999999999, "iat": 0}, "wrong-secret", algorithm="HS256")
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 401

    def test_me_expired_token(self, client):
        _signup(client)
        # Create a token that is already expired
        import datetime
        payload = {
            "sub": "some-id",
            "iat": datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
            "exp": datetime.datetime(2020, 1, 2, tzinfo=datetime.timezone.utc),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 401

    def test_me_nonexistent_user_in_token(self, client):
        token = create_access_token(subject="nonexistent-uuid")
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 401

    def test_me_inactive_user(self, client, db_session):
        _signup(client, email="inactive@example.com")
        user = db_session.query(User).filter(User.email == "inactive@example.com").first()
        user.is_active = False
        db_session.commit()
        token = create_access_token(subject=user.id)
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 401


# ============================================================================
# Database constraints
# ============================================================================


class TestUserModel:
    """Direct model / database tests."""

    def test_user_email_unique_constraint(self, db_session):
        """DB-level unique constraint prevents duplicate emails."""
        from sqlalchemy.exc import IntegrityError

        u1 = User(email="unique@example.com", password_hash=hash_password("pw1"))
        db_session.add(u1)
        db_session.flush()

        u2 = User(email="unique@example.com", password_hash=hash_password("pw2"))
        db_session.add(u2)

        with pytest.raises(IntegrityError):
            db_session.flush()

# ============================================================================
# Rate Limiting
# ============================================================================

class TestRateLimiting:
    """Rate limiting tests."""

    def test_auth_rate_limit(self, client):
        # The limit for auth is 5/minute.
        # Send 5 requests (should succeed/422 but not 429)
        for _ in range(5):
            resp = client.post("/auth/login", json={"email": "limit@example.com", "password": "password"})
            assert resp.status_code != 429

        # 6th request should hit the rate limit
        resp = client.post("/auth/login", json={"email": "limit@example.com", "password": "password"})
        assert resp.status_code == 429
