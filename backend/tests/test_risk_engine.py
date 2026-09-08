import pytest

from services.risk_engine import calculate_deterministic_risk


@pytest.mark.asyncio
async def test_severity_mapping():
    # Test LOW
    res = await calculate_deterministic_risk({"list": [{"main": {"temp": 25}, "wind": {"speed": 2}}]})
    assert res["severity"] == "LOW"

    # Test MODERATE
    res = await calculate_deterministic_risk({"list": [{"main": {"temp": 0}}]})
    assert res["severity"] == "MODERATE"
    assert res["score"] == 40

    # Test HIGH
    res = await calculate_deterministic_risk({"list": [{"main": {"temp": 0}, "wind": {"speed": 20}}]})
    assert res["severity"] == "HIGH"
    assert res["score"] == 70


@pytest.mark.asyncio
async def test_primary_risk_picks_highest_weight_on_tie():
    # Tie between Frost Risk (+40) and Heavy Precipitation (+40)
    # Frost Risk > Heavy Precipitation
    weather = {
        "list": [
            {
                "main": {"temp": 0, "humidity": 50},  # Frost Risk (<2C) -> 40
                "rain": {"3h": 60},  # Heavy Precip (>50) -> 40
                "wind": {"speed": 5},
            }
        ] * 8
    }
    result = await calculate_deterministic_risk(weather)
    assert result["primary_risk"] == "Frost Risk"
    assert result["score"] == 80
    assert result["severity"] == "HIGH"
