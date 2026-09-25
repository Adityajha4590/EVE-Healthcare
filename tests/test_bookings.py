"""Tests for Phase 3 — booking creation, retrieval, authorization, and validation."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.security import create_access_token


# ============================================================================
# Helpers
# ============================================================================


def _signup(client, email="bookuser@example.com", password="securepassword"):
    return client.post("/auth/signup", json={"email": email, "password": password})


def _login(client, email="bookuser@example.com", password="securepassword"):
    return client.post("/auth/login", json={"email": email, "password": password})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_token(client, email="bookuser@example.com"):
    _signup(client, email=email)
    return _login(client, email=email).json()["access_token"]


def _create_centre(client, **overrides):
    data = {
        "name": "Apollo Diagnostics",
        "address": "123 MG Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        **overrides,
    }
    return client.post("/centres", json=data)


def _create_test(client, centre_id, **overrides):
    data = {
        "centre_id": centre_id,
        "name": "Complete Blood Count",
        "price": 1200.00,
        **overrides,
    }
    return client.post("/tests", json=data)


def _tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def _create_booking(client, token, centre_id, test_id, **overrides):
    data = {
        "centre_id": centre_id,
        "test_id": test_id,
        "appointment_date": _tomorrow(),
        "appointment_time": "10:00:00",
        **overrides,
    }
    return client.post("/bookings", json=data, headers=_auth_header(token))


# ============================================================================
# Booking creation
# ============================================================================


class TestBookingCreation:
    """POST /bookings"""

    def test_create_booking_success(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = _create_booking(client, token, centre_id, test_id)
        assert resp.status_code == 201
        data = resp.json()
        assert data["centre_id"] == centre_id
        assert data["test_id"] == test_id
        assert data["status"] == "PENDING"
        assert "id" in data

    def test_booking_gets_correct_user_id(self, client):
        token = _get_token(client, email="bookowner@example.com")
        # Get the user_id from /auth/me
        me = client.get("/auth/me", headers=_auth_header(token)).json()
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = _create_booking(client, token, centre_id, test_id)
        assert resp.json()["user_id"] == me["id"]

    def test_booking_snapshots_price(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id, price=1500.50).json()["id"]

        resp = _create_booking(client, token, centre_id, test_id)
        assert Decimal(str(resp.json()["amount"])) == Decimal("1500.50")

    def test_booking_defaults_to_pending(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = _create_booking(client, token, centre_id, test_id)
        assert resp.json()["status"] == "PENDING"

    def test_appointment_date_stored_correctly(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        tomorrow = _tomorrow()

        resp = _create_booking(
            client, token, centre_id, test_id,
            appointment_date=tomorrow, appointment_time="14:30:00"
        )
        data = resp.json()
        assert data["appointment_date"] == tomorrow
        assert data["appointment_time"] == "14:30:00"

    def test_unauthenticated_booking_rejected(self, client):
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = client.post("/bookings", json={
            "centre_id": centre_id,
            "test_id": test_id,
            "appointment_date": _tomorrow(),
            "appointment_time": "10:00:00",
        })
        assert resp.status_code == 401


# ============================================================================
# Booking validation
# ============================================================================


class TestBookingValidation:
    """Validation rules for POST /bookings"""

    def test_nonexistent_centre_rejected(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = _create_booking(
            client, token, "nonexistent-uuid", test_id
        )
        assert resp.status_code == 404

    def test_inactive_centre_rejected(self, client, db_session):
        from app.models.centre import DiagnosticCentre
        token = _get_token(client)

        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        # Deactivate the centre
        centre = db_session.query(DiagnosticCentre).filter(
            DiagnosticCentre.id == centre_id
        ).first()
        centre.is_active = False
        db_session.commit()

        resp = _create_booking(client, token, centre_id, test_id)
        assert resp.status_code == 400

    def test_nonexistent_test_rejected(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]

        resp = _create_booking(
            client, token, centre_id, "nonexistent-uuid"
        )
        assert resp.status_code == 404

    def test_inactive_test_rejected(self, client, db_session):
        from app.models.test import DiagnosticTest
        token = _get_token(client)

        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        test = db_session.query(DiagnosticTest).filter(
            DiagnosticTest.id == test_id
        ).first()
        test.is_active = False
        db_session.commit()

        resp = _create_booking(client, token, centre_id, test_id)
        assert resp.status_code == 400

    def test_test_from_another_centre_rejected(self, client):
        token = _get_token(client)
        centre_a = _create_centre(client, name="Centre A").json()["id"]
        centre_b = _create_centre(client, name="Centre B").json()["id"]
        test_b = _create_test(client, centre_b, name="Test B").json()["id"]

        # Try to book test_b at centre_a
        resp = _create_booking(client, token, centre_a, test_b)
        assert resp.status_code == 400

    def test_past_appointment_rejected(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        resp = _create_booking(
            client, token, centre_id, test_id,
            appointment_date=yesterday,
        )
        assert resp.status_code == 422

    def test_duplicate_booking_rejected(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp1 = _create_booking(client, token, centre_id, test_id)
        assert resp1.status_code == 201

        resp2 = _create_booking(client, token, centre_id, test_id)
        assert resp2.status_code == 409

    def test_invalid_request_rejected(self, client):
        token = _get_token(client)
        resp = client.post("/bookings", json={}, headers=_auth_header(token))
        assert resp.status_code == 422


# ============================================================================
# Booking retrieval & authorization
# ============================================================================


class TestBookingAuthorization:
    """GET /bookings and GET /bookings/{id}"""

    def test_list_own_bookings(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        _create_booking(client, token, centre_id, test_id)

        resp = client.get("/bookings", headers=_auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_own_booking_by_id(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        booking_id = _create_booking(client, token, centre_id, test_id).json()["id"]

        resp = client.get(f"/bookings/{booking_id}", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == booking_id

    def test_cannot_access_another_users_booking(self, client):
        # User A creates a booking
        token_a = _get_token(client, email="usera@example.com")
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        booking_id = _create_booking(client, token_a, centre_id, test_id).json()["id"]

        # User B tries to access it
        token_b = _get_token(client, email="userb@example.com")
        resp = client.get(f"/bookings/{booking_id}", headers=_auth_header(token_b))
        assert resp.status_code == 403

    def test_list_only_own_bookings(self, client):
        # User A creates a booking
        token_a = _get_token(client, email="usera2@example.com")
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        _create_booking(client, token_a, centre_id, test_id)

        # User B should see zero bookings
        token_b = _get_token(client, email="userb2@example.com")
        resp = client.get("/bookings", headers=_auth_header(token_b))
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_get_nonexistent_booking(self, client):
        token = _get_token(client)
        resp = client.get("/bookings/nonexistent-uuid", headers=_auth_header(token))
        assert resp.status_code == 404

    def test_list_bookings_unauthenticated(self, client):
        resp = client.get("/bookings")
        assert resp.status_code == 401


# ============================================================================
# Security
# ============================================================================


class TestBookingSecurity:
    """Verify the backend ignores client-supplied protected fields."""

    def test_client_cannot_set_user_id(self, client):
        token = _get_token(client, email="real@example.com")
        me = client.get("/auth/me", headers=_auth_header(token)).json()
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        # Try to inject a different user_id in the request body
        resp = client.post("/bookings", json={
            "centre_id": centre_id,
            "test_id": test_id,
            "appointment_date": _tomorrow(),
            "appointment_time": "10:00:00",
            "user_id": "injected-user-id",
        }, headers=_auth_header(token))
        # Pydantic ignores extra fields by default; user_id comes from JWT
        assert resp.status_code == 201
        assert resp.json()["user_id"] == me["id"]

    def test_client_cannot_set_amount(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id, price=1200.00).json()["id"]

        resp = client.post("/bookings", json={
            "centre_id": centre_id,
            "test_id": test_id,
            "appointment_date": _tomorrow(),
            "appointment_time": "10:00:00",
            "amount": 1,  # injected
        }, headers=_auth_header(token))
        assert resp.status_code == 201
        assert Decimal(str(resp.json()["amount"])) == Decimal("1200.00")

    def test_client_cannot_set_status(self, client):
        token = _get_token(client)
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]

        resp = client.post("/bookings", json={
            "centre_id": centre_id,
            "test_id": test_id,
            "appointment_date": _tomorrow(),
            "appointment_time": "10:00:00",
            "status": "CONFIRMED",  # injected
        }, headers=_auth_header(token))
        assert resp.status_code == 201
        assert resp.json()["status"] == "PENDING"
