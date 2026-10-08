import logging
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from conftest import make_intervals
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app import weather as weather_module
from app.config import settings
from app.db import engine
from app.engine import Hazard, InsufficientForecast, Severity
from app.main import app
from app.models import Assessment, Plot

FIELD = {
    "name": "North Field",
    "crop_id": "wheat",
    "stage_id": "wheat.anthesis",
    "location_name": "Pune, India",
    "latitude": 18.52,
    "longitude": 73.85,
    "sowing_date": "2026-01-15",
}


@pytest.fixture
def client():
    with TestClient(app, base_url="http://localhost") as c:
        yield c
    with engine.begin() as conn:
        conn.execute(delete(Assessment))
        conn.execute(delete(Plot))


@pytest.fixture
def weather():
    mock = Mock(return_value=make_intervals(temp=38.0, rh=40.0, wind=5.0))
    with patch("app.assessment.weather.fetch_forecast", mock):
        yield mock


def create_field(client, **changes) -> int:
    resp = client.post("/api/plots", json={**FIELD, **changes})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_health_endpoint(client):
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "changes",
    [
        {"stage_id": "rice.seedling"},
        {"name": "   "},
        {"unexpected_field": "x"},
        {"latitude": 91},
    ],
)
def test_create_rejects_bad_input(client, changes):
    resp = client.post("/api/plots", json={**FIELD, **changes})
    assert resp.status_code == 422
    assert resp.json()["detail"]


def test_plot_crud_workflow(client):
    plot_id = create_field(client)

    dash = client.get("/api/plots").json()
    assert len(dash) == 1
    assert dash[0]["latest_assessment"] is None

    put_resp = client.put(f"/api/plots/{plot_id}", json={**FIELD, "name": "North Field Updated"})
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "North Field Updated"

    assert client.delete(f"/api/plots/{plot_id}").status_code == 204
    assert client.get(f"/api/plots/{plot_id}/assessment").status_code == 404


def test_assessment_endpoint(client, weather):
    plot_id = create_field(client)
    data = client.get(f"/api/plots/{plot_id}/assessment").json()

    assert data["plot"]["name"] == "North Field"
    assert data["assessment"]["score"] == 100
    assert data["assessment"]["severity"] == Severity.HIGH.value
    assert data["assessment"]["primary_hazard"] == Hazard.HEAT.value
    assert len(data["weather"]["intervals"]) == 40
    assert client.get("/api/plots").json()[0]["latest_assessment"]["score"] == 100


def test_new_location_fetches_new_forecast(client, weather):
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/assessment")

    resp = client.put(f"/api/plots/{plot_id}", json={**FIELD, "latitude": 30.9, "longitude": 75.85})
    assert resp.json()["latest_assessment"] is None

    weather.return_value = make_intervals(temp=20.0)
    risk = client.get(f"/api/plots/{plot_id}/assessment").json()
    assert weather.call_count == 2
    assert weather.call_args.args == (30.9, 75.85)
    assert risk["assessment"]["score"] == 0


def test_unusable_forecast_gives_503(client):
    plot_id = create_field(client)
    with patch(
        "app.assessment.weather.fetch_forecast",
        Mock(side_effect=InsufficientForecast("no data")),
    ):
        resp = client.get(f"/api/plots/{plot_id}/assessment")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Weather service unavailable."


def test_weather_key_never_reaches_the_logs(client, caplog, monkeypatch):
    key = "fake-openweather-key-456"
    forecast = (Path(__file__).parent / "fixtures" / "forecast.json").read_text()
    transport = httpx.MockTransport(lambda r: httpx.Response(200, text=forecast))
    real_client = httpx.Client
    monkeypatch.setattr(settings, "OPENWEATHER_API_KEY", key)
    monkeypatch.setattr(
        weather_module.httpx, "Client", lambda **kw: real_client(transport=transport, **kw)
    )
    plot_id = create_field(client)

    with caplog.at_level(logging.DEBUG):
        assert client.get(f"/api/plots/{plot_id}/assessment").status_code == 200
    assert key not in caplog.text
