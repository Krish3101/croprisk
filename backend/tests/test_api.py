from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.domain.engine import ForecastInterval
from app.main import app
from app.security import COOKIE_NAME

# Test database using StaticPool so all connections share the same in-memory DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_workflow(client):
    # 1. Register
    reg_resp = client.post("/api/auth/register", json={"email": "farmer@example.com", "password": "password123"})
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert data["email"] == "farmer@example.com"
    assert COOKIE_NAME not in reg_resp.cookies  # register does not sign in

    # 2. Duplicate register fails with 409 email_taken
    dup_resp = client.post("/api/auth/register", json={"email": "FARMER@EXAMPLE.COM", "password": "password123"})
    assert dup_resp.status_code == 409
    err = dup_resp.json()["error"]
    assert err["code"] == "email_taken"

    # 3. Short password fails with 422 validation_error
    short_pw = client.post("/api/auth/register", json={"email": "other@example.com", "password": "short"})
    assert short_pw.status_code == 422
    assert short_pw.json()["error"]["code"] == "validation_error"
    assert "password" in short_pw.json()["error"]["fields"]

    # 4. /api/auth/me without cookie gives 401 unauthorized
    me_unauth = client.get("/api/auth/me")
    assert me_unauth.status_code == 401
    assert me_unauth.json()["error"]["code"] == "unauthorized"

    # 5. Login with invalid password gives 401 invalid_credentials
    bad_login = client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "wrongpassword"})
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "invalid_credentials"

    # 6. Valid login gives 200 and sets session cookie
    login_resp = client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "password123"})
    assert login_resp.status_code == 200
    assert COOKIE_NAME in login_resp.cookies

    # 7. /api/auth/me with cookie gives 200
    me_resp = client.get("/api/auth/me", cookies=login_resp.cookies)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "farmer@example.com"

    # 8. Logout clears cookie
    logout_resp = client.post("/api/auth/logout", cookies=login_resp.cookies)
    assert logout_resp.status_code == 204


def test_crops_catalogue_endpoint(client):
    client.post("/api/auth/register", json={"email": "user@example.com", "password": "password123"})
    login = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    cookies = login.cookies

    resp = client.get("/api/crops", cookies=cookies)
    assert resp.status_code == 200
    crops = resp.json()
    assert len(crops) == 6
    for c in crops:
        assert len(c["stages"]) == 5


def test_plot_crud_and_isolation(client):
    # User 1
    client.post("/api/auth/register", json={"email": "user1@example.com", "password": "password123"})
    login1 = client.post("/api/auth/login", json={"email": "user1@example.com", "password": "password123"})
    cookies1 = login1.cookies

    # User 2
    client.post("/api/auth/register", json={"email": "user2@example.com", "password": "password123"})
    login2 = client.post("/api/auth/login", json={"email": "user2@example.com", "password": "password123"})
    cookies2 = login2.cookies

    # User 1 creates plot with stage mismatch
    bad_stage_resp = client.post(
        "/api/plots",
        cookies=cookies1,
        json={
            "name": "North Field",
            "crop_id": "wheat",
            "stage_id": "rice.seedling",  # Stage does not belong to wheat!
            "location_name": "Pune, India",
            "latitude": 18.52,
            "longitude": 73.85,
            "sowing_date": "2026-01-15",
        },
    )
    assert bad_stage_resp.status_code == 422
    assert "stage_id" in bad_stage_resp.json()["error"]["fields"]

    # User 1 creates valid plot
    create_resp = client.post(
        "/api/plots",
        cookies=cookies1,
        json={
            "name": "North Field",
            "crop_id": "wheat",
            "stage_id": "wheat.anthesis",
            "location_name": "Pune, India",
            "latitude": 18.52,
            "longitude": 73.85,
            "sowing_date": "2026-01-15",
        },
    )
    assert create_resp.status_code == 201
    plot1_id = create_resp.json()["id"]

    # User 1 views dashboard
    dash1 = client.get("/api/plots", cookies=cookies1)
    assert len(dash1.json()) == 1
    assert dash1.json()[0]["latest_risk"] is None

    # User 2 views dashboard (should see empty array)
    dash2 = client.get("/api/plots", cookies=cookies2)
    assert len(dash2.json()) == 0

    # User 2 tries to access User 1's plot -> 404 (not 403)
    patch_other = client.patch(f"/api/plots/{plot1_id}", cookies=cookies2, json={"name": "Hacked"})
    assert patch_other.status_code == 404
    assert patch_other.json()["error"]["code"] == "not_found"

    delete_other = client.delete(f"/api/plots/{plot1_id}", cookies=cookies2)
    assert delete_other.status_code == 404

    risk_other = client.get(f"/api/plots/{plot1_id}/risk", cookies=cookies2)
    assert risk_other.status_code == 404

    # User 1 patches plot
    patch_own = client.patch(f"/api/plots/{plot1_id}", cookies=cookies1, json={"name": "North Field Updated"})
    assert patch_own.status_code == 200
    assert patch_own.json()["name"] == "North Field Updated"

    # User 1 deletes plot
    del_own = client.delete(f"/api/plots/{plot1_id}", cookies=cookies1)
    assert del_own.status_code == 204

    # Now get gives 404
    assert client.get(f"/api/plots/{plot1_id}/risk", cookies=cookies1).status_code == 404


def test_risk_evaluation_endpoint(client):
    client.post("/api/auth/register", json={"email": "user@example.com", "password": "password123"})
    login = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    cookies = login.cookies

    create_resp = client.post(
        "/api/plots",
        cookies=cookies,
        json={
            "name": "North Field",
            "crop_id": "wheat",
            "stage_id": "wheat.anthesis",
            "location_name": "Pune, India",
            "latitude": 18.52,
            "longitude": 73.85,
            "sowing_date": "2026-01-15",
        },
    )
    plot_id = create_resp.json()["id"]

    mock_forecast = [
        ForecastInterval(
            timestamp=f"2026-09-10T{i*3:02d}:00:00Z",
            temperature_c=38.0,
            relative_humidity=40.0,
            wind_kmh=5.0,
            rain_mm=0.0,
        )
        for i in range(40)
    ]

    with patch("app.services.assessment.weather.fetch_forecast", return_value=mock_forecast):
        risk_resp = client.get(f"/api/plots/{plot_id}/risk", cookies=cookies)
        assert risk_resp.status_code == 200
        data = risk_resp.json()
        assert data["plot"]["name"] == "North Field"
        assert data["risk"]["score"] == 100
        assert data["risk"]["severity"] == "HIGH"
        assert data["risk"]["primary_threat"] == "Extreme Heat"
        assert data["risk"]["is_stale"] is False
        assert data["advisory"]["headline"] != ""
        assert len(data["weather"]["intervals"]) == 40

    # Dashboard now shows latest_risk
    dash = client.get("/api/plots", cookies=cookies)
    assert dash.status_code == 200
    assert dash.json()[0]["latest_risk"]["score"] == 100
