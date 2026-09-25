from app.config import settings


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health response should include status, version, and database fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "database" in data

    def test_health_reports_version(self, client):
        """Health response version should match configured app version."""
        response = client.get("/health")
        data = response.json()

        assert data["version"] == settings.APP_VERSION

    def test_health_database_connected(self, client):
        """Health check should report database as connected."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["database"] == "connected"
