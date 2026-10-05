import dataclasses
import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from conftest import make_intervals

from app.config import settings
from app.domain.engine import AssessmentResult, Threat, WeatherDigest, compute_digest, evaluate
from app.schemas import Advisory
from app.services import advisory
from app.services.catalogue_loader import CROPS, get_crop, get_stage

HAZARD_THREATS = [Threat.HEAT, Threat.FROST, Threat.PRECIP, Threat.WIND, Threat.DISEASE]
DIGEST = WeatherDigest(
    peak_temp_c=35.0,
    min_temp_c=18.0,
    total_rain_mm=10.0,
    max_wind_kmh=25.0,
    peak_humidity_pct=75.0,
    longest_disease_window_h=6,
)
WHEAT = get_crop("wheat")
ANTHESIS = get_stage("wheat", "wheat.anthesis")


def high_result(threat: Threat) -> AssessmentResult:
    return AssessmentResult(
        score=75, severity="HIGH", primary_threat=threat.value, hazard_indices={"heat": 75.0}
    )


def all_text(adv: Advisory) -> str:
    directives = " ".join(a.directive for a in adv.actions)
    return f"{adv.headline} {adv.impact_analysis} {directives} {adv.monitoring_focus}"


def test_low_severity_bypasses_llm_and_fallback():
    result = AssessmentResult(score=25, severity="LOW", primary_threat="None", hazard_indices={})
    res = advisory.build_advisory(result, WHEAT, ANTHESIS, "Pune", 30, DIGEST)
    assert res.source == "bypass"
    assert res.headline == advisory.BYPASS_ADVISORY.headline


@pytest.mark.parametrize("threat", HAZARD_THREATS)
def test_fallback_is_valid_for_every_crop_and_stage(threat):
    for crop in CROPS.values():
        for stage in crop.stages.values():
            adv = advisory.build_fallback_advisory(crop, stage, high_result(threat), DIGEST)
            Advisory.model_validate(adv.model_dump())


def test_frost_fallback_cites_engine_min_temp_and_stage_threshold():
    intervals = make_intervals(temp=8.0)
    intervals[10] = dataclasses.replace(intervals[10], temperature_c=-1.5)
    result = evaluate(intervals, ANTHESIS, WHEAT)
    digest = compute_digest(intervals, WHEAT)
    assert result.primary_threat == Threat.FROST.value

    res = advisory.build_advisory(result, WHEAT, ANTHESIS, "Ludhiana", 60, digest)
    assert res.source == "fallback"
    assert res.impact_analysis == (
        "Over the next five days the lowest temperature is -1.5 °C; "
        f"the threshold for this stage is {ANTHESIS.t_crit_frost} °C. "
        f"Risk score {result.score}/100 ({result.severity})."
    )


def test_advisory_module_has_no_crop_specific_text():
    source = Path(advisory.__file__).read_text(encoding="utf-8").lower()
    for crop in CROPS.values():
        assert crop.id not in source
        assert crop.common_name.lower() not in source


@pytest.mark.parametrize("threat", HAZARD_THREATS)
def test_fallback_has_no_chemicals_or_weekdays(threat):
    text = all_text(
        advisory.build_fallback_advisory(WHEAT, ANTHESIS, high_result(threat), DIGEST)
    ).lower()
    for word in ["fungicide", "pesticide", "herbicide", "insecticide", "kg/ha", "ml/l", "g/l"]:
        assert word not in text
    assert not re.search(r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", text)


def llm_reply(content: dict) -> dict:
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


GOOD_LLM_ADVICE = {
    "headline": "Severe heat at flowering",
    "impact_analysis": "Daytime temperatures well above the stage threshold can dry out pollen.",
    "actions": [{"timeframe": "immediate_24h", "directive": "Irrigate lightly in the evening."}],
    "monitoring_focus": "Look for dried florets after the hot days.",
}


def run_with_llm(status: int, body: dict):
    with (
        patch.object(settings, "OPENROUTER_API_KEY", "fake-test-key"),
        patch("httpx.Client.post") as post,
    ):
        post.return_value.status_code = status
        post.return_value.text = json.dumps(body)
        post.return_value.json.return_value = body
        return advisory.build_advisory(
            high_result(Threat.HEAT), WHEAT, ANTHESIS, "Pune", 60, DIGEST
        )


def test_llm_reply_is_used_when_valid():
    res = run_with_llm(200, llm_reply(GOOD_LLM_ADVICE))
    assert res.source == "llm"
    assert res.headline == "Severe heat at flowering"


def test_invalid_llm_reply_falls_back():
    res = run_with_llm(200, llm_reply({"headline": "short"}))
    assert res.source == "fallback"
    assert res.headline.startswith("Heat stress")


def test_llm_401_falls_back():
    res = run_with_llm(401, {"error": "unauthorised"})
    assert res.source == "fallback"
