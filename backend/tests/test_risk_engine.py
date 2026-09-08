import pytest

from services.risk_engine import calculate_deterministic_risk


@pytest.mark.asyncio
async def test_primary_risk_picks_highest_weight_on_tie():
    weather = {
        "list": [
            {
                "main": {"temp": 28, "humidity": 90},
                "rain": {"3h": 0},
                "wind": {"speed": 15},
            }
        ]
    }
    result = await calculate_deterministic_risk(weather)
    assert result["primary_risk"] == "Storm Conditions"
    assert result["score"] == 65
