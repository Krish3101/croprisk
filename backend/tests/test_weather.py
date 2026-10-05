import contextlib
import copy
import json
import logging
from pathlib import Path

import httpx
import pytest

from app.config import settings
from app.domain.engine import InsufficientForecast
from app.errors import UpstreamUnavailableError
from app.services import weather

FAKE_KEY = "fake-openweather-key-123"
FORECAST = json.loads((Path(__file__).parent / "fixtures" / "forecast.json").read_text())
RealClient = httpx.Client


@pytest.fixture
def respond(monkeypatch):
    """Route weather.py's httpx calls to a handler instead of the network."""
    monkeypatch.setattr(settings, "OPENWEATHER_API_KEY", FAKE_KEY)
    calls: list[httpx.Request] = []

    def install(handler):
        def recording_handler(request):
            calls.append(request)
            return handler(request)

        transport = httpx.MockTransport(recording_handler)
        monkeypatch.setattr(
            weather.httpx, "Client", lambda **kw: RealClient(transport=transport, **kw)
        )
        return calls

    return install


def forecast_with(change) -> dict:
    data = copy.deepcopy(FORECAST)
    change(data["list"])
    return data


def test_recorded_forecast_is_normalised(respond):
    calls = respond(lambda r: httpx.Response(200, json=FORECAST))
    intervals = weather.fetch_forecast(30.9, 75.85)

    assert len(intervals) == 40
    first = intervals[0]
    assert first.timestamp == "2026-09-12T08:00:00+00:00"
    assert first.temperature_c == 27.0
    assert first.relative_humidity == 70.0
    assert round(first.wind_kmh, 2) == round(5.2 * 3.6, 2)  # gust beats speed
    assert intervals[9].rain_mm == 2.4
    assert intervals[0].rain_mm == 0.0
    assert calls[0].url.params["units"] == "metric"


def test_entry_missing_temperature_is_skipped_not_zeroed(respond):
    def drop_last_temp(entries):
        del entries[-1]["main"]["temp"]

    respond(lambda r: httpx.Response(200, json=forecast_with(drop_last_temp)))
    intervals = weather.fetch_forecast(30.9, 75.85)

    assert len(intervals) == 39
    assert min(i.temperature_c for i in intervals) > 15


def test_all_temperatures_missing_is_insufficient(respond):
    def drop_all_temps(entries):
        for e in entries:
            del e["main"]["temp"]

    respond(lambda r: httpx.Response(200, json=forecast_with(drop_all_temps)))
    with pytest.raises(InsufficientForecast):
        weather.fetch_forecast(30.9, 75.85)


def test_non_dict_items_are_skipped(respond):
    def add_junk(entries):
        entries[5] = "junk"
        entries.append(None)

    respond(lambda r: httpx.Response(200, json=forecast_with(add_junk)))
    # Item 5 is gone, so the first unbroken run is items 6..39.
    assert len(weather.fetch_forecast(30.9, 75.85)) == 34


def test_non_dict_payload_is_upstream_error(respond):
    respond(lambda r: httpx.Response(200, json=["not", "a", "forecast"]))
    with pytest.raises(UpstreamUnavailableError):
        weather.fetch_forecast(30.9, 75.85)


def test_html_with_200_is_upstream_error(respond):
    respond(lambda r: httpx.Response(200, text="<html>Service down</html>"))
    with pytest.raises(UpstreamUnavailableError, match="malformed JSON"):
        weather.fetch_forecast(30.9, 75.85)


def test_401_logs_rejected_key(respond, caplog):
    respond(lambda r: httpx.Response(401, json={"cod": 401}))
    with caplog.at_level(logging.WARNING), pytest.raises(UpstreamUnavailableError):
        weather.fetch_forecast(30.9, 75.85)
    assert "OPENWEATHER_API_KEY rejected" in caplog.text


def test_429_is_upstream_error(respond, caplog):
    respond(lambda r: httpx.Response(429, json={"cod": 429}))
    with caplog.at_level(logging.WARNING), pytest.raises(UpstreamUnavailableError, match="rate"):
        weather.fetch_forecast(30.9, 75.85)
    assert "rate limited" in caplog.text


def test_timeout_is_upstream_error(respond):
    def time_out(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    respond(time_out)
    with pytest.raises(UpstreamUnavailableError):
        weather.fetch_forecast(30.9, 75.85)


def test_missing_key_never_calls_out(respond, monkeypatch):
    calls = respond(lambda r: httpx.Response(200, json=FORECAST))
    monkeypatch.setattr(settings, "OPENWEATHER_API_KEY", "")
    with pytest.raises(UpstreamUnavailableError):
        weather.fetch_forecast(30.9, 75.85)
    assert calls == []


def test_geocode_skips_bad_items_and_duplicates(respond):
    places = [
        {"name": "Ludhiana", "state": "Punjab", "country": "IN", "lat": 30.9, "lon": 75.85},
        {"name": "Ludhiana", "state": "Punjab", "country": "IN", "lat": 30.9001, "lon": 75.8501},
        {"name": "No coords", "country": "IN"},
        "junk",
    ]
    respond(lambda r: httpx.Response(200, json=places))
    results = weather.geocode("Ludhiana")

    assert results == [
        {
            "display_name": "Ludhiana, Punjab, IN",
            "city": "Ludhiana",
            "state": "Punjab",
            "country": "IN",
            "latitude": 30.9,
            "longitude": 75.85,
        }
    ]


def read_timeout(request):
    raise httpx.ReadTimeout("slow", request=request)


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(200, json=FORECAST),
        lambda r: httpx.Response(401, json={}),
        lambda r: httpx.Response(500, text="oops"),
        read_timeout,
    ],
)
def test_our_log_lines_never_contain_the_key(respond, caplog, handler):
    respond(handler)
    with (
        caplog.at_level(logging.DEBUG, logger="croprisk"),
        contextlib.suppress(UpstreamUnavailableError),
    ):
        weather.fetch_forecast(30.9, 75.85)
    assert FAKE_KEY not in caplog.text
