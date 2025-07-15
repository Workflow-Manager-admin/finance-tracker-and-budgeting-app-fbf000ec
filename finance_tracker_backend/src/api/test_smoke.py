from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

# PUBLIC_INTERFACE
def test_health_check():
    """Smoke test for health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200


# PUBLIC_INTERFACE
def test_unauthorized_access():
    """Smoke test for protected endpoint returns unauthorized or forbidden."""
    response = client.get("/transactions")
    assert response.status_code in (401, 403, 422)

# TODO: Extend with more endpoint/feature checks as implementation allows.
