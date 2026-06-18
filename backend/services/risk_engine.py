from services.weather_service import get_forecast
from services.ai_service import explain_risk

async def calculate_deterministic_risk(weather_data: dict) -> dict:
    """Calculate risk score strictly based on weather rules."""
    score = 0
    risk_factors = []
    
    # Extract upcoming 5 days data (list of 3-hour forecasts)
    forecasts = weather_data.get("list", [])
    
    max_temp = -100
    min_temp = 100
    max_humidity = 0
    heavy_rain_found = False
    high_wind_found = False
    
    for f in forecasts:
        temp = f.get("main", {}).get("temp", 25)
        humidity = f.get("main", {}).get("humidity", 50)
        rain = f.get("rain", {}).get("3h", 0)
        wind = f.get("wind", {}).get("speed", 0)
        
        max_temp = max(max_temp, temp)
        min_temp = min(min_temp, temp)
        max_humidity = max(max_humidity, humidity)
        
        if rain > 10:
            heavy_rain_found = True
        if wind > 10:
            high_wind_found = True

    # Rule evaluation
    if heavy_rain_found:
        score += 20
        risk_factors.append("Heavy Rain")
        
    if max_humidity > 85:
        score += 15
        risk_factors.append("High Humidity")
        
    if max_temp > 35 or min_temp < 5:
        score += 15
        risk_factors.append("Extreme Temperature")
        
    if high_wind_found:
        score += 25
        risk_factors.append("Storm Conditions")
        
    if max_humidity > 80 and 25 <= max_temp <= 30:
        score += 25
        risk_factors.append("Disease-Prone Conditions")
        
    # Cap score at 100
    score = min(100, score)
    
    if score < 30:
        severity = "LOW"
    elif score <= 70:
        severity = "MODERATE"
    else:
        severity = "HIGH"
        
    primary_risk = risk_factors[-1] if risk_factors else "None"
    
    weather_summary = f"Max Temp: {max_temp}C, Min Temp: {min_temp}C, Max Humidity: {max_humidity}%. "
    if heavy_rain_found:
        weather_summary += "Heavy rain expected. "
    if high_wind_found:
        weather_summary += "High winds expected. "
    
    return {
        "score": score,
        "severity": severity,
        "primary_risk": primary_risk,
        "weather_summary": weather_summary
    }

async def generate_risk_assessment(crop: str, stage: str, city: str) -> dict:
    weather_data = await get_forecast(city)
    risk_data = await calculate_deterministic_risk(weather_data)
    
    if risk_data["severity"] == "LOW" and risk_data["primary_risk"] == "None":
        analysis = "Current weather conditions are optimal. No significant risks identified."
        recommendation = "Continue standard crop maintenance."
    else:
        ai_response = await explain_risk(
            crop, stage, 
            risk_data["score"], risk_data["severity"], 
            risk_data["primary_risk"], risk_data["weather_summary"]
        )
        analysis = ai_response.get("analysis", "")
        recommendation = ai_response.get("recommendation", "")
        
    return {
        "risk_score": risk_data["score"],
        "severity": risk_data["severity"],
        "primary_risk": risk_data["primary_risk"],
        "analysis": analysis,
        "recommendation": recommendation,
        "weather_summary": risk_data["weather_summary"]
    }
