"""Tests for Phase 4 — payments."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest


def _signup(client, email="payuser@example.com", password="securepassword"):
    return client.post("/auth/signup", json={"email": email, "password": password})

def _login(client, email="payuser@example.com", password="securepassword"):
    return client.post("/auth/login", json={"email": email, "password": password})

def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def _get_token(client, email="payuser@example.com"):
    _signup(client, email=email)
    return _login(client, email=email).json()["access_token"]

def _create_centre_and_test(client):
    c = client.post("/centres", json={"name": "C", "address": "A", "city": "C", "state": "S", "pincode": "400001"}).json()
    t = client.post("/tests", json={"centre_id": c["id"], "name": "T", "price": 1000.00}).json()
    return c["id"], t["id"]

def _create_booking(client, token, centre_id, test_id):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return client.post(
        "/bookings",
        json={"centre_id": centre_id, "test_id": test_id, "appointment_date": tomorrow, "appointment_time": "10:00:00"},
        headers=_auth_header(token)
    )

class TestPaymentEndpoints:
    @patch("app.services.payment.simulated_gateway_task")
    def test_initiate_payment(self, mock_task, client):
        token = _get_token(client)
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        resp = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token))
        assert resp.status_code == 202
        data = resp.json()
        assert data["booking_id"] == b_id
        assert data["status"] == "PENDING"
        assert "transaction_id" in data
        assert Decimal(str(data["amount"])) == Decimal("1000.00")

    @patch("app.services.payment.simulated_gateway_task")
    def test_cannot_pay_twice(self, mock_task, client):
        token = _get_token(client)
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token))
        resp2 = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token))
        assert resp2.status_code == 409

    @patch("app.services.payment.simulated_gateway_task")
    def test_cannot_pay_others_booking(self, mock_task, client):
        token1 = _get_token(client, email="u1@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token1, c_id, t_id).json()["id"]

        token2 = _get_token(client, email="u2@example.com")
        resp = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token2))
        assert resp.status_code == 403

    @patch("app.services.payment.simulated_gateway_task")
    def test_get_payment(self, mock_task, client):
        token = _get_token(client)
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        pay_id = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token)).json()["id"]
        
        resp = client.get(f"/payments/{pay_id}", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == pay_id
