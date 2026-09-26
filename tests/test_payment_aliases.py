"""Tests for Payment Alias Endpoints."""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.config import settings
from app.services.payment import generate_webhook_signature
from tests.test_payments import _auth_header, _create_booking, _create_centre_and_test, _get_token

class TestPaymentAliasEndpoints:
    @patch("app.services.payment.simulated_gateway_task")
    def test_initiate_payment_alias(self, mock_task, client):
        token = _get_token(client, email="alias1@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        resp = client.post("/payments/", json={"booking_id": b_id}, headers=_auth_header(token))
        assert resp.status_code == 202
        data = resp.json()
        assert data["booking_id"] == b_id
        assert data["status"] == "PENDING"
        assert "transaction_id" in data
        assert Decimal(str(data["amount"])) == Decimal("1000.00")

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_success_updates_booking_alias(self, mock_task, client):
        token = _get_token(client, email="alias2@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        pay_data = client.post("/payments/", json={"booking_id": b_id}, headers=_auth_header(token)).json()
        txn_id = pay_data["transaction_id"]

        payload = {
            "transaction_id": txn_id,
            "status": "success",
            "amount": "1000.00"
        }
        payload_str = json.dumps(payload)
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)

        resp = client.post(
            "/payments/webhook/",
            content=payload_str,
            headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp.status_code == 200

        # Check booking is CONFIRMED
        b_resp = client.get(f"/bookings/{b_id}", headers=_auth_header(token)).json()
        assert b_resp["status"] == "CONFIRMED"

        # Check payment is SUCCESS
        p_resp = client.get(f"/payments/{pay_data['id']}", headers=_auth_header(token)).json()
        assert p_resp["status"] == "SUCCESS"

    @patch("app.services.payment.simulated_gateway_task")
    def test_initiate_payment_alias_unauthorized(self, mock_task, client):
        # Without auth
        resp = client.post("/payments/", json={"booking_id": "some_id"})
        assert resp.status_code == 401

    @patch("app.services.payment.simulated_gateway_task")
    def test_initiate_payment_alias_invalid_booking(self, mock_task, client):
        token = _get_token(client, email="alias3@example.com")
        resp = client.post("/payments/", json={"booking_id": "00000000-0000-0000-0000-000000000000"}, headers=_auth_header(token))
        assert resp.status_code == 404

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_alias_invalid_signature(self, mock_task, client):
        payload_str = json.dumps({"transaction_id": "txn_123", "status": "success", "amount": "1000.00"})
        resp = client.post(
            "/payments/webhook/",
            content=payload_str,
            headers={"X-Webhook-Signature": "wrong", "Content-Type": "application/json"}
        )
        assert resp.status_code == 401

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_alias_idempotency(self, mock_task, client):
        token = _get_token(client, email="alias4@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        txn_id = client.post("/payments/", json={"booking_id": b_id}, headers=_auth_header(token)).json()["transaction_id"]

        payload = {"transaction_id": txn_id, "status": "success", "amount": "1000.00"}
        payload_str = json.dumps(payload)
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)

        resp1 = client.post("/payments/webhook/", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp1.status_code == 200

        # Sending exactly the same payload again should be 200 (idempotent)
        resp2 = client.post("/payments/webhook/", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp2.status_code == 200

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_alias_malformed_payload(self, mock_task, client):
        payload_str = "not json"
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)
        resp = client.post(
            "/payments/webhook/",
            content=payload_str,
            headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp.status_code == 422
