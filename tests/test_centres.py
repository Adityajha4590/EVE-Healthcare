"""Tests for Phase 3 — diagnostic catalogue (centres and tests)."""

from decimal import Decimal

import pytest


# ============================================================================
# Helpers
# ============================================================================


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


# ============================================================================
# Centres
# ============================================================================


class TestCentres:
    """GET/POST /centres"""

    def test_create_centre(self, client):
        resp = _create_centre(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Apollo Diagnostics"
        assert data["pincode"] == "400001"
        assert data["is_active"] is True
        assert "id" in data

    def test_list_centres(self, client):
        _create_centre(client, name="Centre A")
        _create_centre(client, name="Centre B")
        resp = client.get("/centres")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_centre_by_id(self, client):
        centre_id = _create_centre(client).json()["id"]
        resp = client.get(f"/centres/{centre_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == centre_id

    def test_get_nonexistent_centre(self, client):
        resp = client.get("/centres/nonexistent-uuid")
        assert resp.status_code == 404

    def test_inactive_centre_hidden_from_list(self, client, db_session):
        from app.models.centre import DiagnosticCentre

        centre = DiagnosticCentre(
            name="Inactive Centre",
            address="Nowhere",
            city="Ghost",
            state="None",
            pincode="000000",
            is_active=False,
        )
        db_session.add(centre)
        db_session.flush()

        resp = client.get("/centres")
        ids = [c["id"] for c in resp.json()]
        assert centre.id not in ids

    def test_invalid_pincode_rejected(self, client):
        resp = _create_centre(client, pincode="12345")
        assert resp.status_code == 422

        resp = _create_centre(client, pincode="abcdef")
        assert resp.status_code == 422

    def test_pagination(self, client):
        for i in range(5):
            _create_centre(client, name=f"PagCentre{i}")
        resp = client.get("/centres?page=1&page_size=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ============================================================================
# Tests
# ============================================================================


class TestDiagnosticTests:
    """Diagnostic test CRUD and catalogue"""

    def test_create_test(self, client):
        centre_id = _create_centre(client).json()["id"]
        resp = _create_test(client, centre_id)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Complete Blood Count"
        assert Decimal(str(data["price"])) == Decimal("1200.00")
        assert data["centre_id"] == centre_id

    def test_list_tests_for_centre(self, client):
        centre_id = _create_centre(client).json()["id"]
        _create_test(client, centre_id, name="Test A")
        _create_test(client, centre_id, name="Test B")
        resp = client.get(f"/centres/{centre_id}/tests")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_test_by_id(self, client):
        centre_id = _create_centre(client).json()["id"]
        test_id = _create_test(client, centre_id).json()["id"]
        resp = client.get(f"/tests/{test_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == test_id

    def test_get_nonexistent_test(self, client):
        resp = client.get("/tests/nonexistent-uuid")
        assert resp.status_code == 404

    def test_inactive_test_hidden_from_centre_listing(self, client, db_session):
        from app.models.test import DiagnosticTest

        centre_id = _create_centre(client).json()["id"]
        inactive_test = DiagnosticTest(
            centre_id=centre_id,
            name="Hidden Test",
            price=Decimal("500.00"),
            is_active=False,
        )
        db_session.add(inactive_test)
        db_session.flush()

        resp = client.get(f"/centres/{centre_id}/tests")
        ids = [t["id"] for t in resp.json()]
        assert inactive_test.id not in ids

    def test_list_tests_for_nonexistent_centre(self, client):
        resp = client.get("/centres/nonexistent-uuid/tests")
        assert resp.status_code == 404

    def test_price_is_decimal(self, client):
        centre_id = _create_centre(client).json()["id"]
        resp = _create_test(client, centre_id, price=1500.50)
        data = resp.json()
        assert Decimal(str(data["price"])) == Decimal("1500.50")

    def test_price_must_be_positive(self, client):
        centre_id = _create_centre(client).json()["id"]
        resp = _create_test(client, centre_id, price=0)
        assert resp.status_code == 422

        resp = _create_test(client, centre_id, price=-100)
        assert resp.status_code == 422
