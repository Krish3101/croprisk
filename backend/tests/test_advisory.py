import json
from unittest.mock import patch

from app.config import settings
from app.domain.crops import CROPS, get_crop, get_stage
from app.domain.engine import AssessmentResult, WeatherDigest
from app.schemas import Advisory
from app.services import advice_data, advisory, weather


def dummy_digest() -> WeatherDigest:
    return WeatherDigest(
        peak_temp_c=35.0,
        min_temp_c=18.0,
        total_rain_mm=10.0,
        max_wind_kmh=25.0,
        peak_humidity_pct=75.0,
        longest_disease_window_h=6,
    )


def test_advisory_bypass_below_30():
    crop = get_crop("wheat")
    stage = get_stage("wheat", "wheat.anthesis")
    result = AssessmentResult(
        score=25,
        severity="LOW",
        primary_threat="None",
        hazard_indices={"heat": 0.0, "frost": 0.0, "precip": 0.0, "disease": 0.0, "wind": 0.0},
    )
    res = advisory.build_advisory(result, crop, stage, "Pune, India", 30, dummy_digest())
    assert res.source == "bypass"
    assert "tolerance" in res.headline.lower() or "normal" in res.headline.lower()


def test_all_30_fallbacks_exist_and_validate():
    threats = [
        "Extreme Heat",
        "Frost Damage",
        "Excess Precipitation",
        "Fungal Disease Pressure",
        "Wind Lodging",
    ]
    crops = list(CROPS.keys())
    assert len(crops) == 6

    for crop_id in crops:
        for threat in threats:
            adv = advice_data.get_fallback_advisory(crop_id, threat)
            assert isinstance(adv, Advisory)
            assert 10 <= len(adv.headline) <= 120
            assert 40 <= len(adv.impact_analysis) <= 350
            assert 1 <= len(adv.actions) <= 2
            for action in adv.actions:
                assert action.timeframe in ("immediate_24h", "preventative_72h")
                assert 15 <= len(action.directive) <= 200
            assert 15 <= len(adv.monitoring_focus) <= 150

    # Generic fallback when threat is None at score >= 30
    generic = advice_data.get_fallback_advisory("wheat", "None")
    assert isinstance(generic, Advisory)


def test_fallback_free_of_chemical_names_and_doses():
    prohibited_words = [
        "fungicide", "pesticide", "herbicide", "insecticide",
        "mancozeb", "chlorpyrifos", "glyphosate", "imidacloprid",
        "carbendazim", "ml/l", "g/l", "kg/ha", "litres per",
    ]
    for key, adv in advice_data.FALLBACK_ADVISORIES.items():
        text = f"{adv.headline} {adv.impact_analysis} {' '.join(a.directive for a in adv.actions)} {adv.monitoring_focus}".lower()
        for bad in prohibited_words:
            assert bad not in text, f"Found prohibited word '{bad}' in fallback for {key}"


def test_advisory_llm_success():
    crop = get_crop("wheat")
    stage = get_stage("wheat", "wheat.anthesis")
    result = AssessmentResult(
        score=75,
        severity="HIGH",
        primary_threat="Extreme Heat",
        hazard_indices={"heat": 85.0, "frost": 0.0, "precip": 0.0, "disease": 0.0, "wind": 0.0},
    )

    mock_llm_json = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "headline": "Severe Heat Warning for Flowering Wheat",
                        "impact_analysis": "Daytime temperatures over 34 C cause pollen desiccation and floret sterility during anthesis, threatening severe grain yield loss.",
                        "actions": [
                            {
                                "timeframe": "immediate_24h",
                                "directive": "Apply light evening sprinkler irrigation to dampen the canopy and lower midday temperatures.",
                            }
                        ],
                        "monitoring_focus": "Inspect flowering spikes for dried florets.",
                    })
                }
            }
        ]
    }

    with (
        patch.object(settings, "OPENROUTER_API_KEY", "fake-test-key"),
        patch("httpx.Client.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_llm_json

        res = advisory.build_advisory(result, crop, stage, "Pune, India", 60, dummy_digest())
        assert res.source == "llm"
        assert "Severe Heat Warning" in res.headline


def test_advisory_llm_retry_and_fallback():
    crop = get_crop("wheat")
    stage = get_stage("wheat", "wheat.anthesis")
    result = AssessmentResult(
        score=75,
        severity="HIGH",
        primary_threat="Extreme Heat",
        hazard_indices={"heat": 85.0, "frost": 0.0, "precip": 0.0, "disease": 0.0, "wind": 0.0},
    )

    # Malformed response (missing required fields)
    bad_llm_json = {"choices": [{"message": {"content": "{\"headline\": \"short\"}"}}]}

    with (
        patch.object(settings, "OPENROUTER_API_KEY", "fake-test-key"),
        patch("httpx.Client.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = bad_llm_json

        res = advisory.build_advisory(result, crop, stage, "Pune, India", 60, dummy_digest())
        # Retried once, failed twice -> falls back to deterministic
        assert mock_post.call_count == 2
        assert res.source == "fallback"
        assert "Extreme Heat Advisory for Wheat" in res.headline


def test_weather_normalization():
    # Mock openweather API response
    raw_data = {
        "list": [
            {
                "dt": 1773316800,
                "main": {"temp": 28.5, "humidity": 65},
                "wind": {"speed": 4.0, "gust": 7.0},  # gust > speed -> 7.0 * 3.6 = 25.2 km/h
                "rain": {"3h": 12.5},
            },
            {
                "dt": 1773327600,
                "main": {"temp": 26.0, "humidity": 70},
                "wind": {"speed": 5.0},  # no gust -> speed * 3.6 = 18.0 km/h
                # missing rain -> 0.0
            },
        ]
    }

    with (
        patch.object(settings, "OPENWEATHER_API_KEY", "fake-key"),
        patch("httpx.Client.get") as mock_get,
    ):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = raw_data

        intervals = weather.fetch_forecast(18.52, 73.85)
        assert len(intervals) == 2

        assert intervals[0].temperature_c == 28.5
        assert intervals[0].relative_humidity == 65.0
        assert round(intervals[0].wind_kmh, 1) == 25.2
        assert intervals[0].rain_mm == 12.5

        assert intervals[1].temperature_c == 26.0
        assert intervals[1].relative_humidity == 70.0
        assert round(intervals[1].wind_kmh, 1) == 18.0
        assert intervals[1].rain_mm == 0.0
