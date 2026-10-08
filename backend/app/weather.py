"""OpenWeather geocoding and the 5-day / 3-hour forecast, checked and normalised."""

import datetime
import logging

import httpx
from fastapi import HTTPException

from app.config import settings
from app.engine import ForecastInterval, InsufficientForecast

logger = logging.getLogger("croprisk")

CADENCE_SECONDS = 3 * 3600
MIN_INTERVALS = 8  # 24 h of data


UNAVAILABLE = "Weather service unavailable."


def _get_json(url: str, params: dict):
    """GET an OpenWeather endpoint. Any failure becomes a 503."""
    if not settings.OPENWEATHER_API_KEY:
        raise HTTPException(503, UNAVAILABLE)
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params={**params, "appid": settings.OPENWEATHER_API_KEY})
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        # str(exc) can include the URL, which has the key in it, so log the type only
        logger.warning("OpenWeather request failed: %s", type(exc).__name__)
        raise HTTPException(503, UNAVAILABLE) from None


def geocode(query: str) -> list[dict]:
    """Up to 5 places matching the query, without duplicates."""
    query = query.strip()
    if not query:
        return []
    items = _get_json("https://api.openweathermap.org/geo/1.0/direct", {"q": query, "limit": 5})
    if not isinstance(items, list):
        raise HTTPException(503, UNAVAILABLE)

    results: list[dict] = []
    seen: set[tuple[float, float]] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            lat, lon = float(item["lat"]), float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if (round(lat, 3), round(lon, 3)) in seen:
            continue
        seen.add((round(lat, 3), round(lon, 3)))

        name, state, country = item.get("name", ""), item.get("state"), item.get("country")
        parts = [p for p in [name, state, country] if p]
        results.append(
            {
                "display_name": ", ".join(parts) if parts else f"{lat:.4f}, {lon:.4f}",
                "city": name or None,
                "state": state,
                "country": country,
                "latitude": lat,
                "longitude": lon,
            }
        )
    return results[:5]


def _parse_entry(entry) -> tuple[int, ForecastInterval] | None:
    """One forecast entry, or None if it is missing data we can't default."""
    if not isinstance(entry, dict):
        return None
    main = entry.get("main")
    wind = entry.get("wind")
    if not isinstance(main, dict) or not isinstance(wind, dict):
        return None
    try:
        dt = int(entry["dt"])
        temp = float(main["temp"])
        rh = float(main["humidity"])
        speed = float(wind["speed"])
        gust = float(wind.get("gust", speed))
    except (KeyError, TypeError, ValueError):
        return None

    # Only rain may default to 0: OpenWeather leaves it out when it doesn't rain.
    rain = entry.get("rain")
    try:
        rain_mm = float(rain.get("3h", 0.0)) if isinstance(rain, dict) else 0.0
    except (TypeError, ValueError):
        rain_mm = 0.0

    return dt, ForecastInterval(
        timestamp=datetime.datetime.fromtimestamp(dt, datetime.UTC).isoformat(),
        temperature_c=temp,
        relative_humidity=rh,
        wind_kmh=max(speed, gust) * 3.6,
        rain_mm=rain_mm,
    )


def fetch_forecast(latitude: float, longitude: float) -> list[ForecastInterval]:
    """The first run of at least 8 valid intervals on a 3-hour cadence.

    Bad entries are skipped, never filled with zeros, so missing data can't look like frost.
    """
    data = _get_json(
        "https://api.openweathermap.org/data/2.5/forecast",
        {"lat": latitude, "lon": longitude, "units": "metric"},
    )
    entries = data.get("list") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise HTTPException(503, UNAVAILABLE)

    parsed = sorted((p for p in map(_parse_entry, entries) if p is not None), key=lambda p: p[0])
    run: list[ForecastInterval] = []
    prev_dt = None
    for dt, interval in parsed:
        if prev_dt is not None and dt - prev_dt < CADENCE_SECONDS:
            continue  # duplicate or off-cadence entry
        if prev_dt is not None and dt - prev_dt > CADENCE_SECONDS:
            if len(run) >= MIN_INTERVALS:
                break
            run = []  # gap: start a new run
        run.append(interval)
        prev_dt = dt

    if len(run) < MIN_INTERVALS:
        raise InsufficientForecast(
            f"Only {len(run)} consecutive valid 3-hour intervals, need {MIN_INTERVALS}."
        )
    return run
