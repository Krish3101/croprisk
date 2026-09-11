"""Pure risk engine for CropRisk. No database, no network, no framework imports."""

import math
from dataclasses import dataclass

from app.domain.crops import CropConfig, StageConfig, get_crop


class InsufficientForecast(Exception):
    """Raised when the forecast interval list is empty."""


@dataclass(frozen=True)
class ForecastInterval:
    timestamp: str
    temperature_c: float
    relative_humidity: float
    wind_kmh: float
    rain_mm: float


@dataclass(frozen=True)
class WeatherDigest:
    peak_temp_c: float
    min_temp_c: float
    total_rain_mm: float
    max_wind_kmh: float
    peak_humidity_pct: float
    longest_disease_window_h: int


@dataclass(frozen=True)
class AssessmentResult:
    score: int
    severity: str
    primary_threat: str
    hazard_indices: dict[str, float]


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def _round_half_up(n: float) -> int:
    return math.floor(n + 0.5)


def _compute_longest_run_hours(
    intervals: list[ForecastInterval],
    rh_crit: float,
    t_min_dis: float,
    t_max_dis: float,
) -> int:
    longest_run = 0
    current_run = 0
    for interval in intervals:
        matches = (
            interval.relative_humidity >= rh_crit
            and t_min_dis <= interval.temperature_c <= t_max_dis
        )
        if matches:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return longest_run * 3


def compute_digest(
    intervals: list[ForecastInterval],
    crop: CropConfig,
) -> WeatherDigest:
    if not intervals:
        raise InsufficientForecast("Forecast intervals cannot be empty.")

    peak_temp = max(i.temperature_c for i in intervals)
    min_temp = min(i.temperature_c for i in intervals)
    total_rain = round(sum(i.rain_mm for i in intervals), 1)
    max_wind = max(i.wind_kmh for i in intervals)
    peak_rh = max(i.relative_humidity for i in intervals)
    disease_hours = _compute_longest_run_hours(
        intervals, crop.rh_crit, crop.t_min_dis, crop.t_max_dis
    )

    return WeatherDigest(
        peak_temp_c=round(peak_temp, 1),
        min_temp_c=round(min_temp, 1),
        total_rain_mm=round(total_rain, 1),
        max_wind_kmh=round(max_wind, 1),
        peak_humidity_pct=round(peak_rh, 1),
        longest_disease_window_h=disease_hours,
    )


def evaluate(
    intervals: list[ForecastInterval],
    stage: StageConfig,
    crop: CropConfig | None = None,
) -> AssessmentResult:
    """Evaluate crop risk against normalised weather intervals.

    Pure function: same inputs -> same outputs, always.
    """
    if not intervals:
        raise InsufficientForecast("Forecast intervals cannot be empty.")

    crop_id = stage.id.split(".")[0]
    if crop is None:
        crop = get_crop(crop_id)
        if crop is None:
            raise ValueError(f"Unknown crop for stage {stage.id}")

    # 1. Heat
    delta_t_peak = max(0.0, max(i.temperature_c - stage.t_crit_heat for i in intervals))
    dh = sum(max(0.0, i.temperature_c - stage.t_crit_heat) * 3 for i in intervals)
    i_heat = (
        _clamp01(delta_t_peak / (stage.t_lethal_heat - stage.t_crit_heat)) * 70.0
        + _clamp01(dh / 36.0) * 30.0
    )

    # 2. Frost
    min_t = min(i.temperature_c for i in intervals)
    i_frost = _clamp01((stage.t_crit_frost - min_t) / (stage.t_crit_frost - stage.t_lethal_frost)) * 100.0

    # 3. Excess precipitation
    rain_values = [i.rain_mm for i in intervals]
    if len(rain_values) < 8:
        r24_max = sum(rain_values)
    else:
        r24_max = max(sum(rain_values[k : k + 8]) for k in range(len(rain_values) - 7))
    i_precip = _clamp01((r24_max - stage.r_crit_24h) / (stage.r_flood_24h - stage.r_crit_24h)) * 100.0

    # 4. Fungal disease
    l_hours = _compute_longest_run_hours(intervals, crop.rh_crit, crop.t_min_dis, crop.t_max_dis)
    i_disease = 0.0 if l_hours < 12 else min(100.0, 30.0 + ((l_hours - 12) / 24.0) * 70.0)

    # 5. Wind lodging
    max_w = max(i.wind_kmh for i in intervals)
    i_wind = _clamp01((max_w - stage.w_crit_lodge) / (stage.w_severe - stage.w_crit_lodge)) * 100.0

    # Score, Severity, Primary Threat
    w_heat, w_frost, w_precip, w_disease, w_wind = stage.weights
    c_heat = w_heat * i_heat
    c_frost = w_frost * i_frost
    c_precip = w_precip * i_precip
    c_disease = w_disease * i_disease
    c_wind = w_wind * i_wind

    s_wsum = c_heat + c_frost + c_precip + c_disease + c_wind
    w_max = max(stage.weights)
    max_c = max(c_heat, c_frost, c_precip, c_disease, c_wind)
    r_dom = max_c / w_max if w_max > 0 else 0.0

    score = _round_half_up(min(100.0, max(s_wsum, r_dom)))

    if score <= 29:
        severity = "LOW"
    elif score <= 65:
        severity = "MODERATE"
    else:
        severity = "HIGH"

    # Biological tie-break order: Frost (5) > Heat (4) > Precip (3) > Wind (2) > Disease (1)
    if max_c == 0.0:
        primary_threat = "None"
    else:
        candidates = [
            (c_frost, 5, "Frost Damage"),
            (c_heat, 4, "Extreme Heat"),
            (c_precip, 3, "Excess Precipitation"),
            (c_wind, 2, "Wind Lodging"),
            (c_disease, 1, "Fungal Disease Pressure"),
        ]
        # max by value, then biological tie-break priority
        _, _, primary_threat = max(candidates, key=lambda item: (item[0], item[1]))

    return AssessmentResult(
        score=score,
        severity=severity,
        primary_threat=primary_threat,
        hazard_indices={
            "heat": i_heat,
            "frost": i_frost,
            "precip": i_precip,
            "disease": i_disease,
            "wind": i_wind,
        },
    )
