"""Advice text: fixed text at low risk, else the LLM, else a rule-based fallback.

The score is already final here. Every path only explains it.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import asdict
from typing import NamedTuple

import httpx

from app.config import settings
from app.domain.catalogue import CropConfig, StageConfig
from app.domain.engine import (
    DISEASE_MIN_RUN_HOURS,
    AssessmentResult,
    Severity,
    Threat,
    WeatherDigest,
)
from app.schemas import Action, Advisory, AdvisoryResponse

logger = logging.getLogger("croprisk")

SYSTEM_PROMPT = """You are CropRisk's agronomic advisor. You write short, practical guidance for smallholder farmers.

1. GROUND TRUTH: the risk score, severity band and primary threat you are given are already calculated and correct. Never recalculate or dispute them.
2. STAGE SPECIFICITY: explain the damage mechanism for the exact crop and growth stage given.
3. NO CHEMICAL PRESCRIPTIONS: never name a pesticide, herbicide or fungicide, and never give a dose. Recommend cultural, mechanical, irrigation or biological measures, or advise consulting the local extension officer.
4. ACTIONABLE: assume hand tools, furrow or sprinkler irrigation, family labour.
5. BRIEF: this is read on a phone during a weather emergency. No preamble.
Produce valid JSON matching this schema:
{
  "headline": "...",
  "impact_analysis": "...",
  "actions": [{"timeframe": "immediate_24h"|"preventative_72h", "directive": "..."}],
  "monitoring_focus": "..."
}"""

# Free on OpenRouter. If OpenRouter retires it, this is the one line to change.
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

BYPASS_ADVISORY = Advisory(
    headline="No weather risk this week",
    impact_analysis="No weather hazard crosses this stage's tolerance thresholds in the next five days.",
    actions=[
        Action(
            timeframe="preventative_72h",
            directive="Carry on with normal field work and planned schedule.",
        )
    ],
    monitoring_focus="Keep up standard checks on soil moisture and vegetative health.",
)


class HazardText(NamedTuple):
    name: str
    metric: str  # what the digest number is, e.g. "lowest temperature"
    value: Callable[[WeatherDigest], float]
    limit: Callable[[CropConfig, StageConfig], float]
    limit_text: str  # what the threshold means, e.g. "this stage's 24 h rain limit"
    unit: str
    now: str  # action for the next 24 h
    later: str  # action for the next 72 h


FALLBACK_TABLE = {
    Threat.HEAT: HazardText(
        "Heat stress", "peak temperature", lambda d: d.peak_temp_c,
        lambda c, s: s.t_crit_heat, "the threshold for this stage", " °C",
        "Irrigate lightly in the evening if water is available, to cool the crop.",
        "Check the crop after the hottest day for scorched or wilted leaves.",
    ),
    Threat.FROST: HazardText(
        "Frost", "lowest temperature", lambda d: d.min_temp_c,
        lambda c, s: s.t_crit_frost, "the threshold for this stage", " °C",
        "Irrigate in the afternoon before the coldest night; moist soil holds more heat.",
        "Check young growth for frost damage after the coldest night.",
    ),
    Threat.PRECIP: HazardText(
        "Heavy rain", "total rain", lambda d: d.total_rain_mm,
        lambda c, s: s.r_crit_24h, "this stage's limit for any 24 h", " mm",
        "Clear drains and field outlets before the heaviest rain.",
        "Walk the low spots after the rain and drain any standing water.",
    ),
    Threat.WIND: HazardText(
        "Strong wind", "strongest wind", lambda d: d.max_wind_kmh,
        lambda c, s: s.w_crit_lodge, "this stage's lodging limit", " km/h",
        "Postpone spraying and other field work during the windiest period.",
        "Check for flattened or broken plants after the strong winds.",
    ),
    Threat.DISEASE: HazardText(
        "Fungal disease", "longest humid spell", lambda d: d.longest_disease_window_h,
        lambda c, s: DISEASE_MIN_RUN_HOURS, "disease risk starts after", " h",
        "Avoid evening irrigation while the air stays humid.",
        "Look at the lower leaves for spots and ask your local extension officer if you see any.",
    ),
}  # fmt: skip


def build_fallback_advisory(
    crop: CropConfig, stage: StageConfig, result: AssessmentResult, digest: WeatherDigest
) -> Advisory:
    """Explain the score using only the engine's numbers and this stage's thresholds."""
    row = FALLBACK_TABLE.get(Threat(result.primary_threat))
    if row is None:
        return BYPASS_ADVISORY
    value, limit = row.value(digest), row.limit(crop, stage)
    return Advisory(
        headline=f"{row.name} risk for {crop.common_name} at {stage.name}",
        impact_analysis=(
            f"Over the next five days the {row.metric} is {value}{row.unit}; "
            f"{row.limit_text} is {limit}{row.unit}. "
            f"Risk score {result.score}/100 ({result.severity})."
        ),
        actions=[
            Action(timeframe="immediate_24h", directive=row.now),
            Action(timeframe="preventative_72h", directive=row.later),
        ],
        monitoring_focus=f"Watch the {row.metric}; {row.limit_text} is {limit}{row.unit}.",
    )


def _call_openrouter(user_facts_json: str) -> Advisory | None:
    """One call to OpenRouter; None on any failure or invalid reply."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_facts_json},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "reasoning": {"enabled": False},
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                json=payload,
            )
            if resp.status_code != 200:
                logger.warning("OpenRouter returned %s: %s", resp.status_code, resp.text[:500])
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            return Advisory.model_validate_json(content)
    except Exception as exc:
        logger.warning("OpenRouter call or validation failed: %s", exc)
        return None


def build_advisory(
    result: AssessmentResult,
    crop: CropConfig,
    stage: StageConfig,
    location_name: str,
    days_after_sowing: int,
    digest: WeatherDigest,
) -> AdvisoryResponse:
    if result.severity == Severity.LOW:
        return AdvisoryResponse(**BYPASS_ADVISORY.model_dump(), source="bypass")

    if settings.OPENROUTER_API_KEY:
        facts = {
            "crop": {"common_name": crop.common_name, "scientific_name": crop.scientific_name},
            "stage": {
                "name": stage.name,
                "bbch": stage.bbch,
                "heat_threshold_c": stage.t_crit_heat,
                "frost_threshold_c": stage.t_crit_frost,
            },
            "field": {"location": location_name, "days_after_sowing": days_after_sowing},
            "assessment": {
                "score": result.score,
                "severity": result.severity,
                "primary_threat": result.primary_threat,
                "hazard_indices": {k: round(v, 1) for k, v in result.hazard_indices.items()},
            },
            "weather_digest": asdict(digest),
        }
        llm_advisory = _call_openrouter(json.dumps(facts))
        if llm_advisory is not None:
            return AdvisoryResponse(**llm_advisory.model_dump(), source="llm")

    fallback = build_fallback_advisory(crop, stage, result, digest)
    return AdvisoryResponse(**fallback.model_dump(), source="fallback")
