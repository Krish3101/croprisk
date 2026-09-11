"""Weather service: geocoding and 5-day / 3-hour forecast normalization."""

import datetime

import httpx

from app.config import settings
from app.domain.engine import ForecastInterval, InsufficientForecast
from app.errors import UpstreamUnavailableError


def geocode(query: str) -> list[dict]:
    """Search for locations using OpenWeatherMap Geocoding API."""
    clean_query = query.strip()
    if not clean_query:
        return []

    if not settings.OPENWEATHER_API_KEY:
        raise UpstreamUnavailableError("Weather service API key is not configured.")

    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": clean_query,
        "limit": 5,
        "appid": settings.OPENWEATHER_API_KEY,
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                raise UpstreamUnavailableError(f"Geocoding provider returned status {resp.status_code}")
            items = resp.json()
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise UpstreamUnavailableError("Geocoding service timed out or failed.") from exc

    results: list[dict] = []
    seen: set[tuple[float, float]] = set()

    for item in items:
        lat = float(item.get("lat", 0.0))
        lon = float(item.get("lon", 0.0))
        key = (round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)

        name = item.get("name", "")
        state = item.get("state")
        country = item.get("country")

        parts = [p for p in [name, state, country] if p]
        display_name = ", ".join(parts) if parts else f"{lat:.4f}, {lon:.4f}"

        results.append({
            "display_name": display_name,
            "city": name or None,
            "state": state,
            "country": country,
            "country_code": country,
            "latitude": lat,
            "longitude": lon,
        })
        if len(results) >= 5:
            break

    return results


def fetch_forecast(latitude: float, longitude: float) -> list[ForecastInterval]:
    """Fetch 5-day / 3-hour forecast and normalise to pure ForecastInterval objects."""
    if not settings.OPENWEATHER_API_KEY:
        raise UpstreamUnavailableError("Weather service API key is not configured.")

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": latitude,
        "lon": longitude,
        "units": "metric",
        "appid": settings.OPENWEATHER_API_KEY,
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                raise UpstreamUnavailableError(f"Weather forecast provider returned status {resp.status_code}")
            data = resp.json()
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise UpstreamUnavailableError("Weather forecast service timed out or failed.") from exc

    entries = data.get("list", [])
    if not entries:
        raise InsufficientForecast("Weather provider returned empty forecast intervals.")

    intervals: list[ForecastInterval] = []
    for entry in entries:
        dt = entry.get("dt")
        if dt:
            ts = datetime.datetime.fromtimestamp(dt, datetime.UTC).isoformat()
        else:
            ts = entry.get("dt_txt", "")

        main = entry.get("main", {})
        temp = float(main.get("temp", 0.0))
        rh = float(main.get("humidity", 0.0))

        wind_data = entry.get("wind", {})
        speed = float(wind_data.get("speed", 0.0))
        gust = float(wind_data.get("gust", speed))
        wind_kmh = max(speed, gust) * 3.6

        rain_data = entry.get("rain", {})
        rain_mm = float(rain_data.get("3h", 0.0)) if isinstance(rain_data, dict) else 0.0

        intervals.append(
            ForecastInterval(
                timestamp=ts,
                temperature_c=temp,
                relative_humidity=rh,
                wind_kmh=wind_kmh,
                rain_mm=rain_mm,
            )
        )

    return intervals
