from services.ai_service import explain_risk
from services.weather_service import get_forecast


async def calculate_deterministic_risk(weather_data: dict) -> dict:
    """Calculate risk score strictly based on weather rules."""
    score = 0
    forecasts = weather_data.get("list", [])

    heavy_precip = False
    extreme_heat = False
    frost_risk = False
    high_wind = False
    disease_pressure = False

    # Check immediate simple thresholds
    for f in forecasts:
        temp = f.get("main", {}).get("temp", 25)
        wind_mps = f.get("wind", {}).get("speed", 0)
        wind_kmh = wind_mps * 3.6
        if temp > 35:
            extreme_heat = True
        if temp < 2:
            frost_risk = True
        if wind_kmh > 60:
            high_wind = True

    # Check Heavy Precipitation (>50mm in 24h) using 8-block (24h) rolling windows
    for i in range(len(forecasts) - 7):
        window = forecasts[i : i + 8]
        total_rain = sum(f.get("rain", {}).get("3h", 0) for f in window)
        if total_rain > 50:
            heavy_precip = True
            break

    # Check Disease Pressure (Humidity > 85% & Temp 20-30°C for > 12h) using 5-block (15h) rolling windows
    for i in range(len(forecasts) - 4):
        window = forecasts[i : i + 5]
        if len(window) == 5 and all(
            f.get("main", {}).get("humidity", 0) > 85 and 20 <= f.get("main", {}).get("temp", 0) <= 30
            for f in window
        ):
            disease_pressure = True
            break

    triggered = []

    if heavy_precip:
        triggered.append(("Heavy Precipitation", 40))
    if extreme_heat:
        triggered.append(("Extreme Heat", 35))
    if frost_risk:
        triggered.append(("Frost Risk", 40))
    if high_wind:
        triggered.append(("High Wind", 30))
    if disease_pressure:
        triggered.append(("Disease Pressure", 45))

    for _, weight in triggered:
        score += weight

    score = min(100, score)

    if score <= 30:
        severity = "LOW"
    elif score <= 65:
        severity = "MODERATE"
    else:
        severity = "HIGH"

    # Primary Threat Tie-Break Order: Frost Risk > Extreme Heat > High Wind > Heavy Precipitation > Disease Pressure
    tie_break = {
        "Frost Risk": 5,
        "Extreme Heat": 4,
        "High Wind": 3,
        "Heavy Precipitation": 2,
        "Disease Pressure": 1
    }

    if not triggered:
        primary_risk = "None"
    else:
        max_weight = max(w for _, w in triggered)
        top_candidates = [t for t, w in triggered if w == max_weight]
        primary_risk = max(top_candidates, key=lambda t: tie_break.get(t, 0))

    weather_summary = "Forecast analysis complete."
    if triggered:
        weather_summary = "Triggered conditions: " + ", ".join(t for t, _ in triggered)

    return {
        "score": score,
        "severity": severity,
        "primary_risk": primary_risk,
        "weather_summary": weather_summary,
    }


async def generate_risk_assessment(crop: str, stage: str, lat: float, lon: float) -> dict:
    weather_data = await get_forecast(lat, lon)
    risk_data = await calculate_deterministic_risk(weather_data)

    if risk_data["severity"] == "LOW" and risk_data["primary_risk"] == "None":
        analysis = "Current weather conditions are optimal. No significant risks identified."
        recommendation = "Continue standard crop maintenance."
    else:
        ai_response = await explain_risk(
            crop,
            stage,
            risk_data["score"],
            risk_data["severity"],
            risk_data["primary_risk"],
            risk_data["weather_summary"],
        )
        analysis = ai_response.get("analysis", "")
        recommendation = ai_response.get("recommendation", "")

    return {
        "risk_score": risk_data["score"],
        "severity": risk_data["severity"],
        "primary_risk": risk_data["primary_risk"],
        "analysis": analysis,
        "recommendation": recommendation,
        "weather_summary": risk_data["weather_summary"],
    }
