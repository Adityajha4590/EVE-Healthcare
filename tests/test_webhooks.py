"""Tests for Phase 4 — webhooks."""

import json
from unittest.mock import patch

import pytest

from app.config import settings
from app.services.payment import generate_webhook_signature
from tests.test_payments import _auth_header, _create_booking, _create_centre_and_test, _get_token


class TestWebhooks:
    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_success_updates_booking(self, mock_task, client):
        token = _get_token(client, email="wh1@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        pay_data = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token)).json()
        txn_id = pay_data["transaction_id"]

        payload = {
            "transaction_id": txn_id,
            "status": "success",
            "amount": "1000.00"
        }
        payload_str = json.dumps(payload)
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)

        resp = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp.status_code == 200

        # Check booking is CONFIRMED
        b_resp = client.get(f"/bookings/{b_id}", headers=_auth_header(token)).json()
        assert b_resp["status"] == "CONFIRMED"

        # Check payment is SUCCESS
        p_resp = client.get(f"/payments/{pay_data['id']}", headers=_auth_header(token)).json()
        assert p_resp["status"] == "SUCCESS"

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_idempotency(self, mock_task, client):
        token = _get_token(client, email="wh2@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        txn_id = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token)).json()["transaction_id"]

        payload = {"transaction_id": txn_id, "status": "success", "amount": "1000.00"}
        payload_str = json.dumps(payload)
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)

        resp1 = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp1.status_code == 200

        # Sending exactly the same payload again should be 200 (idempotent)
        resp2 = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp2.status_code == 200

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_invalid_signature(self, mock_task, client):
        token = _get_token(client, email="wh3@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        txn_id = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token)).json()["transaction_id"]

        payload = {"transaction_id": txn_id, "status": "success", "amount": "1000.00"}
        payload_str = json.dumps(payload)

        # Send with wrong sig
        resp = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": "invalid", "Content-Type": "application/json"})
        assert resp.status_code == 401

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_amount_mismatch(self, mock_task, client):
        token = _get_token(client, email="wh4@example.com")
        c_id, t_id = _create_centre_and_test(client)
        b_id = _create_booking(client, token, c_id, t_id).json()["id"]

        pay_data = client.post(f"/bookings/{b_id}/pay", headers=_auth_header(token)).json()
        txn_id = pay_data["transaction_id"]

        # Simulate tampered amount
        payload = {"transaction_id": txn_id, "status": "success", "amount": "1.00"}
        payload_str = json.dumps(payload)
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)

        resp = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp.status_code == 200
        # It's an internal error handler that returns 200 but fails the payment.
        
        p_resp = client.get(f"/payments/{pay_data['id']}", headers=_auth_header(token)).json()
        assert p_resp["status"] == "FAILED"
        assert p_resp["failure_reason"] == "Amount mismatch in webhook"

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_invalid_signature_malformed_json(self, mock_task, client):
        resp = client.post("/webhooks/payments", content="not json", headers={"X-Webhook-Signature": "invalid", "Content-Type": "application/json"})
        assert resp.status_code == 401

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_missing_signature_malformed_json(self, mock_task, client):
        resp = client.post("/webhooks/payments", content="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 401

    @patch("app.services.payment.simulated_gateway_task")
    def test_webhook_valid_signature_malformed_json(self, mock_task, client):
        payload_str = "not json"
        sig = generate_webhook_signature(payload_str, settings.WEBHOOK_SECRET)
        resp = client.post("/webhooks/payments", content=payload_str, headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"})
        assert resp.status_code == 422
