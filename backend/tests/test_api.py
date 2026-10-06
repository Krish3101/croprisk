import datetime
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from conftest import make_intervals
from fastapi.testclient import TestClient
from sqlalchemy import delete, text, update

import app.main as main_module
from app.config import settings
from app.db import engine, make_engine
from app.domain.engine import InsufficientForecast, Severity, Threat
from app.main import app
from app.models import Plot, RiskAssessment
from app.services import weather as weather_module

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
        conn.execute(delete(RiskAssessment))
        conn.execute(delete(Plot))


@pytest.fixture
def weather():
    mock = Mock(return_value=make_intervals(temp=38.0, rh=40.0, wind=5.0))
    with patch("app.services.assessment.weather.fetch_forecast", mock):
        yield mock


def create_field(client, **changes) -> int:
    resp = client.post("/api/plots", json={**FIELD, **changes})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_health_endpoint(client):
    data = client.get("/api/health").json()
    assert data["status"] == "ok"
    assert data["db"] is True
    assert data["schema_version"] == 3
    assert len(data["catalogue_version"]) == 12


def test_database_uses_wal(client):
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA user_version")).scalar() == 3


def test_crops_catalogue_endpoint(client):
    crops = client.get("/api/crops").json()
    assert len(crops) == 6
    assert all(len(c["stages"]) == 5 for c in crops)


def test_unknown_host_rejected(client):
    resp = client.get("/api/crops", headers={"Host": "evil.com"})
    assert resp.status_code == 400


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
    assert resp.json()["error"]["code"] == "validation_error"


def test_plot_crud_workflow(client):
    plot_id = create_field(client)

    dash = client.get("/api/plots").json()
    assert len(dash) == 1
    assert dash[0]["latest_risk"] is None

    patch_resp = client.patch(f"/api/plots/{plot_id}", json={"name": "North Field Updated"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "North Field Updated"

    assert client.delete(f"/api/plots/{plot_id}").status_code == 204
    assert client.get(f"/api/plots/{plot_id}/risk").status_code == 404


def test_huge_id_rejected(client):
    assert client.get(f"/api/plots/{10**22}/risk").status_code == 422


def test_patch_null_rejected(client):
    plot_id = create_field(client)
    resp = client.patch(f"/api/plots/{plot_id}", json={"name": None})
    assert resp.status_code == 422


def test_empty_patch_does_not_touch_updated_at(client):
    plot_id = create_field(client)
    with engine.connect() as conn:
        before = conn.execute(text("SELECT updated_at FROM plots")).scalar()

    assert client.patch(f"/api/plots/{plot_id}", json={}).status_code == 200
    with engine.connect() as conn:
        assert conn.execute(text("SELECT updated_at FROM plots")).scalar() == before


def test_risk_endpoint(client, weather):
    plot_id = create_field(client)
    data = client.get(f"/api/plots/{plot_id}/risk").json()

    assert data["plot"]["name"] == "North Field"
    assert data["risk"]["score"] == 100
    assert data["risk"]["severity"] == Severity.HIGH.value
    assert data["risk"]["primary_threat"] == Threat.HEAT.value
    assert data["risk"]["is_stale"] is False
    assert data["refreshed"] is True
    assert len(data["weather"]["intervals"]) == 40
    assert client.get("/api/plots").json()[0]["latest_risk"]["score"] == 100


def test_get_with_refresh_param_does_not_refresh(client, weather):
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/risk")
    resp = client.get(f"/api/plots/{plot_id}/risk?refresh=true")

    assert weather.call_count == 1
    assert resp.json()["refreshed"] is False


def test_two_refreshes_inside_cooldown_make_one_call(client, weather):
    plot_id = create_field(client)
    first = client.post(f"/api/plots/{plot_id}/risk/refresh").json()
    second = client.post(f"/api/plots/{plot_id}/risk/refresh")

    assert weather.call_count == 1
    assert first["refreshed"] is True
    assert second.status_code == 200
    assert second.json()["refreshed"] is False


def test_patch_stage_rescores_without_network_call(client, weather):
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/risk")

    resp = client.patch(f"/api/plots/{plot_id}", json={"stage_id": "wheat.ripening"})
    assert resp.json()["latest_risk"]["score"] == 17
    assert client.get("/api/plots").json()[0]["latest_risk"]["score"] == 17
    assert weather.call_count == 1


def test_list_never_calls_llm_and_detail_rescores_with_it(client, weather, monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    llm = Mock(side_effect=lambda facts: None)
    monkeypatch.setattr("app.services.advisory._call_openrouter", llm)
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/risk")
    assert llm.call_count == 1

    # A stage change makes the stored row out of date; the list scores it without the LLM.
    client.patch(f"/api/plots/{plot_id}", json={"stage_id": "wheat.grain_fill"})
    listed = client.get("/api/plots").json()
    assert listed[0]["latest_risk"] is not None
    assert llm.call_count == 1

    # The risk route re-scores the row with the LLM advisory, still without a new forecast.
    detail = client.get(f"/api/plots/{plot_id}/risk").json()
    assert llm.call_count == 2
    assert weather.call_count == 1
    # The in-memory list score matches what the risk route saved.
    assert listed[0]["latest_risk"]["score"] == detail["risk"]["score"]
    assert listed[0]["latest_risk"]["severity"] == detail["risk"]["severity"]


def test_patch_location_fetches_new_forecast(client, weather):
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/risk")

    resp = client.patch(f"/api/plots/{plot_id}", json={"latitude": 30.9, "longitude": 75.85})
    assert resp.json()["latest_risk"] is None

    weather.return_value = make_intervals(temp=20.0)
    risk = client.get(f"/api/plots/{plot_id}/risk").json()
    assert weather.call_count == 2
    assert weather.call_args.args == (30.9, 75.85)
    assert risk["risk"]["score"] == 0


@pytest.mark.parametrize(("hours", "expected"), [(20, True), (49, None)])
def test_dashboard_shows_old_score_as_stale_up_to_48_hours(client, weather, hours, expected):
    plot_id = create_field(client)
    client.get(f"/api/plots/{plot_id}/risk")
    old = (datetime.datetime.now(UTC) - datetime.timedelta(hours=hours)).isoformat()
    with engine.begin() as conn:
        conn.execute(update(RiskAssessment).values(forecast_fetched_at=old, created_at=old))

    latest = client.get("/api/plots").json()[0]["latest_risk"]
    assert (latest and latest["is_stale"]) == expected


def test_stage_missing_from_catalogue_returns_409(client, weather):
    plot_id = create_field(client)
    with engine.begin() as conn:
        conn.execute(text("UPDATE plots SET stage_id = 'wheat.removed'"))

    resp = client.get(f"/api/plots/{plot_id}/risk")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "catalogue_mismatch"
    assert weather.call_count == 0


def test_error_envelopes(client):
    put_resp = client.put("/api/plots/1")
    assert put_resp.status_code == 405
    assert put_resp.json()["error"]["code"] == "method_not_allowed"

    malformed = client.post(
        "/api/plots", content="not json {", headers={"Content-Type": "application/json"}
    )
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "validation_error"


def test_old_database_refuses_to_start(tmp_path, monkeypatch):
    old = make_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with old.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR)"))
        conn.execute(text("CREATE TABLE plots (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL)"))
    monkeypatch.setattr(main_module, "engine", old)

    with (
        pytest.raises(
            RuntimeError, match=r"schema v0 found, expected 3: run ./scripts/start.sh --reset"
        ),
        TestClient(app, base_url="http://localhost"),
    ):
        pass


def test_empty_database_is_created_at_current_version(tmp_path, monkeypatch):
    fresh = make_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    monkeypatch.setattr(main_module, "engine", fresh)

    with TestClient(app, base_url="http://localhost"):
        pass
    with fresh.connect() as conn:
        assert conn.execute(text("PRAGMA user_version")).scalar() == 3


def test_two_first_loads_at_once_make_one_call(client):
    def slow_forecast(lat, lon):
        time.sleep(0.2)
        return make_intervals(temp=20.0)

    plot_id = create_field(client)
    weather = Mock(side_effect=slow_forecast)
    with (
        patch("app.services.assessment.weather.fetch_forecast", weather),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        futures = [pool.submit(client.get, f"/api/plots/{plot_id}/risk") for _ in range(2)]
        statuses = [f.result().status_code for f in futures]

    assert statuses == [200, 200]
    assert weather.call_count == 1


def test_unusable_forecast_gives_503(client):
    plot_id = create_field(client)
    with patch(
        "app.services.assessment.weather.fetch_forecast",
        Mock(side_effect=InsufficientForecast("no data")),
    ):
        resp = client.get(f"/api/plots/{plot_id}/risk")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "upstream_unavailable"


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
        assert client.get(f"/api/plots/{plot_id}/risk").status_code == 200
    assert key not in caplog.text
