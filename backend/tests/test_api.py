import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from main import app
from models.database import Base, engine, get_db

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "KisanAI running"


def test_register_and_login():
    response = client.post(
        "/api/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200

    response = client.post(
        "/api/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_plot_crud():
    # Login
    response = client.post(
        "/api/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create plot
    plot_data = {
        "name": "Test Plot",
        "crop_type": "Wheat",
        "location": "Pune",
        "growth_stage": "Vegetative",
        "sowing_date": "2023-01-01",
    }
    from unittest.mock import patch
    with patch("routes.plots.geocode_location") as mock_geo:
        mock_geo.return_value = [{"lat": 18.52, "lon": 73.85}]
        response = client.post("/api/plots", json=plot_data, headers=headers)
    assert response.status_code == 200
    plot_id = response.json()["id"]

    # Get plots
    response = client.get("/api/plots", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["latest_risk"] is None

    # Test Tenant Isolation
    response_other = client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "password123"}
    )
    response_other = client.post(
        "/api/auth/login", data={"username": "other@example.com", "password": "password123"}
    )
    token_other = response_other.json()["access_token"]
    headers_other = {"Authorization": f"Bearer {token_other}"}

    # Other user should see 0 plots
    response = client.get("/api/plots", headers=headers_other)
    assert len(response.json()) == 0

    # Other user trying to access this plot should get 404
    response = client.patch(
        f"/api/plots/{plot_id}", json={"growth_stage": "Flowering"}, headers=headers_other
    )
    assert response.status_code == 404

    # Update plot
    with patch("routes.plots.geocode_location") as mock_geo:
        mock_geo.return_value = [{"lat": 18.52, "lon": 73.85}]
        response = client.patch(
            f"/api/plots/{plot_id}", json={"growth_stage": "Flowering"}, headers=headers
        )
    assert response.status_code == 200
    assert response.json()["growth_stage"] == "Flowering"

    # Test assessment generation & invalidation
    with patch("routes.risk.generate_risk_assessment") as mock_generate:
        mock_generate.return_value = {
            "risk_score": 10,
            "severity": "LOW",
            "primary_risk": "None",
            "analysis": "Test analysis",
            "recommendation": "Test recommendation",
            "weather_summary": "Test summary"
        }
        res = client.get(f"/api/plots/{plot_id}/risk", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_stale"] is False
        assert mock_generate.call_count == 1

        # Request again, should hit cache
        res = client.get(f"/api/plots/{plot_id}/risk", headers=headers)
        assert mock_generate.call_count == 1

        # Update plot location, should invalidate cache
        with patch("routes.plots.geocode_location") as mock_geo:
            mock_geo.return_value = [{"lat": 19.0, "lon": 73.0}]
            client.patch(f"/api/plots/{plot_id}", json={"location": "Mumbai"}, headers=headers)

        # Request risk again, should generate new
        res = client.get(f"/api/plots/{plot_id}/risk", headers=headers)
        assert mock_generate.call_count == 2
