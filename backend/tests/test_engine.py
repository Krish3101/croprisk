import datetime
from datetime import UTC, timedelta

import pytest

from app.domain.catalogue import StageConfig
from app.domain.engine import (
    ForecastInterval,
    InsufficientForecast,
    Severity,
    Threat,
    compute_digest,
    evaluate,
)
from app.services.catalogue_loader import get_crop, get_stage


def make_constant_forecast(
    temp_c: float,
    rh: float,
    wind_kmh: float,
    rain_mm: float,
    count: int = 40,
    start: datetime.datetime | None = None,
) -> list[ForecastInterval]:
    if start is None:
        start = datetime.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
    return [
        ForecastInterval(
            timestamp=(start + timedelta(hours=i * 3)).isoformat(),
            temperature_c=temp_c,
            relative_humidity=rh,
            wind_kmh=wind_kmh,
            rain_mm=rain_mm,
        )
        for i in range(count)
    ]


# Golden vectors: worked derivations in docs/engine.md
def test_golden_vector_1():
    """wheat.anthesis, T=38, RH=40, Wind=5, Rain=0 -> Score=100, HIGH, Extreme Heat."""
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    intervals = make_constant_forecast(38.0, 40.0, 5.0, 0.0)
    result = evaluate(intervals, stage, crop)

    assert result.score == 100
    assert result.severity == Severity.HIGH.value
    assert result.primary_threat == Threat.HEAT.value
    assert round(result.hazard_indices["heat"], 1) == 100.0
    assert round(result.hazard_indices["frost"], 1) == 0.0
    assert round(result.hazard_indices["precip"], 1) == 0.0
    assert round(result.hazard_indices["disease"], 1) == 0.0
    assert round(result.hazard_indices["wind"], 1) == 0.0


def test_golden_vector_2():
    """wheat.anthesis, T=-1, RH=50, Wind=10, Rain=0 -> Score=57, MODERATE, Frost Damage."""
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    intervals = make_constant_forecast(-1.0, 50.0, 10.0, 0.0)
    result = evaluate(intervals, stage, crop)

    assert result.score == 57
    assert result.severity == Severity.MODERATE.value
    assert result.primary_threat == Threat.FROST.value
    assert round(result.hazard_indices["frost"], 1) == 66.7
    assert round(result.hazard_indices["heat"], 1) == 0.0


def test_golden_vector_3():
    """rice.tillering, T=27, RH=90, Wind=10, Rain=0 -> Score=100, HIGH, Fungal Disease Pressure."""
    stage = get_stage("rice", "rice.tillering")
    crop = get_crop("rice")
    intervals = make_constant_forecast(27.0, 90.0, 10.0, 0.0)
    result = evaluate(intervals, stage, crop)

    assert result.score == 100
    assert result.severity == Severity.HIGH.value
    assert result.primary_threat == Threat.DISEASE.value
    assert round(result.hazard_indices["disease"], 1) == 100.0


def test_golden_vector_4():
    """wheat.anthesis, T=20, RH=50, Wind=10, Rain=0 -> Score=0, LOW, None."""
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    intervals = make_constant_forecast(20.0, 50.0, 10.0, 0.0)
    result = evaluate(intervals, stage, crop)

    assert result.score == 0
    assert result.severity == Severity.LOW.value
    assert result.primary_threat == Threat.NONE.value
    for idx_val in result.hazard_indices.values():
        assert round(idx_val, 1) == 0.0


def test_golden_vector_5():
    """wheat.ripening, T=38, RH=40, Wind=5, Rain=0 -> Score=17, LOW, Extreme Heat."""
    stage = get_stage("wheat", "wheat.ripening")
    crop = get_crop("wheat")
    intervals = make_constant_forecast(38.0, 40.0, 5.0, 0.0)
    result = evaluate(intervals, stage, crop)

    assert result.score == 17
    assert result.severity == Severity.LOW.value
    assert result.primary_threat == Threat.HEAT.value
    assert round(result.hazard_indices["heat"], 1) == 60.0


def test_golden_vector_6():
    """cotton.harvest, T=25, RH=90, Wind=55, Rain=3.75 -> Score=65, MODERATE, Excess Precipitation.

    Tests:
    - S_wsum (65.0) beats R_dom (50.0).
    - C_precip == C_wind == 25.0 tie-break resolves to Excess Precipitation.
    - Score 65 pins the top edge of MODERATE.
    """
    stage = get_stage("cotton", "cotton.harvest")
    crop = get_crop("cotton")
    intervals = make_constant_forecast(25.0, 90.0, 55.0, 3.75)
    result = evaluate(intervals, stage, crop)

    assert result.score == 65
    assert result.severity == Severity.MODERATE.value
    assert result.primary_threat == Threat.PRECIP.value
    assert round(result.hazard_indices["precip"], 1) == 50.0
    assert round(result.hazard_indices["disease"], 1) == 100.0
    assert round(result.hazard_indices["wind"], 1) == 100.0


# Time-varying golden vectors (7-10)
def test_golden_vector_7_rolling_24h_rain_burst():
    """wheat.anthesis: rolling 24h window (8 intervals) with rain burst in middle.

    Stage thresholds: r_crit_24h = 35.0 mm, r_flood_24h = 75.0 mm.
    Forecast: 40 intervals.
    Intervals 0-11: 2 mm each (24 mm across first 12 intervals, max 8-window = 16 mm).
    Intervals 12-19 (exact 8-interval 24h burst): 7.0 mm each -> 8 * 7.0 = 56.0 mm.
    Intervals 20-39: 0 mm.
    Total 5-day rain = 24 + 56 = 80 mm (> flood limit), but max 24h rolling sum = 56.0 mm.
    I_precip = (56.0 - 35.0) / (75.0 - 35.0) * 100 = 21 / 40 * 100 = 52.5.
    Weights for wheat.anthesis: precip weight = 0.15. Max weight = 0.35 (heat).
    C_precip = 0.15 * 52.5 = 7.875.
    R_dom = 7.875 / 0.35 = 22.5.
    S_wsum = 7.875.
    Score = round_half_up(max(7.875, 22.5)) = 23.
    """
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    start = datetime.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
    intervals: list[ForecastInterval] = []
    for i in range(40):
        rain = 2.0 if i < 12 else (7.0 if 12 <= i < 20 else 0.0)
        intervals.append(
            ForecastInterval(
                timestamp=(start + timedelta(hours=i * 3)).isoformat(),
                temperature_c=20.0,
                relative_humidity=50.0,
                wind_kmh=10.0,
                rain_mm=rain,
            )
        )

    result = evaluate(intervals, stage, crop)
    assert round(result.hazard_indices["precip"], 1) == 52.5
    assert result.score == 23
    assert result.severity == Severity.LOW.value
    assert result.primary_threat == Threat.PRECIP.value


def test_golden_vector_8_longest_humidity_run():
    """wheat.anthesis: disease run length with interrupted windows.

    Crop thresholds: rh_crit = 80.0, t_min_dis = 15.0, t_max_dis = 25.0.
    Intervals 0-2 (3 blocks = 9h): favorable (RH 85%, T 20°C).
    Interval 3 (3h): dry break (RH 65%, T 20°C) -> resets run!
    Intervals 4-9 (6 blocks = 18h): continuous favorable (RH 85%, T 20°C).
    Interval 10-39: dry (RH 60%).
    Longest run is 18h.
    I_disease = 30.0 + ((18 - 12) / 24.0) * 70.0 = 30 + 0.25 * 70 = 47.5.
    Wheat.anthesis weights: disease weight = 0.15, max weight = 0.35.
    C_disease = 0.15 * 47.5 = 7.125.
    R_dom = 7.125 / 0.35 = 20.357.
    Score = round_half_up(max(7.125, 20.357)) = 20.
    """
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    start = datetime.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
    intervals: list[ForecastInterval] = []
    for i in range(40):
        rh = 85.0 if (i < 3 or 4 <= i <= 9) else 60.0
        intervals.append(
            ForecastInterval(
                timestamp=(start + timedelta(hours=i * 3)).isoformat(),
                temperature_c=20.0,
                relative_humidity=rh,
                wind_kmh=10.0,
                rain_mm=0.0,
            )
        )

    result = evaluate(intervals, stage, crop)
    assert round(result.hazard_indices["disease"], 1) == 47.5
    assert result.score == 20
    assert result.severity == Severity.LOW.value
    assert result.primary_threat == Threat.DISEASE.value


def test_golden_vector_9_diurnal_heat_accumulation():
    """maize.silking: variable temperatures accumulating degree-hours.

    Stage thresholds: t_crit_heat = 34.0°C, t_lethal_heat = 39.0°C.
    T peaks at 36.0°C (delta_peak = 2.0).
    Peak component = (2.0 / 5.0) * 70.0 = 28.0.
    4 afternoon intervals (i=4, 12, 20, 28) reach 36.0°C (+2°C above crit).
    DH = 4 * (2.0 * 3) = 24.0 degree-hours.
    Duration component = (24.0 / 36.0) * 30.0 = 20.0.
    I_heat = 28.0 + 20.0 = 48.0.
    Maize.silking weights: heat=0.40, frost=0.20, precip=0.15, disease=0.10, wind=0.15. Max weight = 0.40.
    C_heat = 0.40 * 48.0 = 19.2.
    R_dom = 19.2 / 0.40 = 48.0.
    Score = round_half_up(max(19.2, 48.0)) = 48.
    Severity = MODERATE (score 48 <= 65).
    """
    stage = get_stage("maize", "maize.silking")
    crop = get_crop("maize")
    start = datetime.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
    intervals: list[ForecastInterval] = []
    for i in range(40):
        t = 36.0 if i in (4, 12, 20, 28) else 28.0
        intervals.append(
            ForecastInterval(
                timestamp=(start + timedelta(hours=i * 3)).isoformat(),
                temperature_c=t,
                relative_humidity=50.0,
                wind_kmh=10.0,
                rain_mm=0.0,
            )
        )

    result = evaluate(intervals, stage, crop)
    assert round(result.hazard_indices["heat"], 1) == 48.0
    assert result.score == 48
    assert result.severity == Severity.MODERATE.value
    assert result.primary_threat == Threat.HEAT.value


def test_golden_vector_10_boundary_pinning_29():
    """Boundary test pinning score exactly at 29 (top edge of LOW)."""
    # mustard.flowering: frost t_crit = 2.0, t_lethal = -2.0.
    # At min temp 0.68°C:
    # I_frost = (2.0 - 0.68) / 4.0 * 100 = 1.32 / 4.0 * 100 = 33.0.
    # Weights for mustard.flowering: frost weight = 0.35 (max weight).
    # C_frost = 0.35 * 33.0 = 11.55.
    # R_dom = 11.55 / 0.35 = 33.0 -> score = 33.
    # To get score = 29.0:
    # R_dom = 29.0 -> I_frost = 29.0 -> (2.0 - min_t)/4.0 = 0.29 -> 2.0 - min_t = 1.16 -> min_t = 0.84°C.
    stage = get_stage("mustard", "mustard.flowering")
    crop = get_crop("mustard")
    intervals = make_constant_forecast(temp_c=20.0, rh=50.0, wind_kmh=10.0, rain_mm=0.0)
    intervals[5] = ForecastInterval(
        timestamp=intervals[5].timestamp,
        temperature_c=0.84,
        relative_humidity=50.0,
        wind_kmh=10.0,
        rain_mm=0.0,
    )
    result = evaluate(intervals, stage, crop)
    assert result.score == 29
    assert result.severity == Severity.LOW.value
    assert result.primary_threat == Threat.FROST.value


def test_empty_intervals_raises():
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    with pytest.raises(InsufficientForecast):
        evaluate([], stage, crop)
    with pytest.raises(InsufficientForecast):
        compute_digest([], crop)


def test_hazard_heat_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    res_below = evaluate(make_constant_forecast(25.0, 40.0, 5.0, 0.0), stage, crop)
    assert res_below.hazard_indices["heat"] == 0.0

    intervals = [ForecastInterval("t0", 30.5, 40.0, 5.0, 0.0)] + [
        ForecastInterval(f"t{i}", 20.0, 40.0, 5.0, 0.0) for i in range(1, 40)
    ]
    res_mid = evaluate(intervals, stage, crop)
    assert 0.0 < res_mid.hazard_indices["heat"] < 100.0

    res_lethal = evaluate(make_constant_forecast(35.0, 40.0, 5.0, 0.0), stage, crop)
    assert res_lethal.hazard_indices["heat"] == 100.0


def test_hazard_frost_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    res_above = evaluate(make_constant_forecast(5.0, 40.0, 5.0, 0.0), stage, crop)
    assert res_above.hazard_indices["frost"] == 0.0

    res_mid = evaluate(make_constant_forecast(0.0, 40.0, 5.0, 0.0), stage, crop)
    assert round(res_mid.hazard_indices["frost"], 1) == 33.3

    res_lethal = evaluate(make_constant_forecast(-3.0, 40.0, 5.0, 0.0), stage, crop)
    assert res_lethal.hazard_indices["frost"] == 100.0


def test_hazard_precip_fewer_than_8_blocks():
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    intervals = [ForecastInterval(f"t{i}", 20.0, 40.0, 5.0, 10.0) for i in range(5)]
    res = evaluate(intervals, stage, crop)
    assert round(res.hazard_indices["precip"], 1) == 37.5


def test_hazard_wind_thresholds():
    stage = get_stage("wheat", "wheat.anthesis")
    crop = get_crop("wheat")
    res_below = evaluate(make_constant_forecast(20.0, 40.0, 30.0, 0.0), stage, crop)
    assert res_below.hazard_indices["wind"] == 0.0

    res_mid = evaluate(make_constant_forecast(20.0, 40.0, 52.5, 0.0), stage, crop)
    assert round(res_mid.hazard_indices["wind"], 1) == 50.0

    res_high = evaluate(make_constant_forecast(20.0, 40.0, 70.0, 0.0), stage, crop)
    assert res_high.hazard_indices["wind"] == 100.0


def test_tie_break_biological_order():
    """Verify tie-break Frost > Heat > Precip > Wind > Disease."""
    stage_tie_frost_heat = StageConfig(
        id="wheat.custom",
        name="Custom",
        bbch="00",
        order=1,
        t_crit_heat=30.0,
        t_lethal_heat=40.0,
        t_crit_frost=5.0,
        t_lethal_frost=-5.0,
        r_crit_24h=50.0,
        r_flood_24h=100.0,
        w_crit_lodge=40.0,
        w_severe=80.0,
        weights=(0.5, 0.5, 0.0, 0.0, 0.0),
    )
    intervals = [
        ForecastInterval("t0", 40.0, 40.0, 10.0, 0.0),
        ForecastInterval("t1", -5.0, 40.0, 10.0, 0.0),
    ] + [ForecastInterval(f"t{i}", 20.0, 40.0, 10.0, 0.0) for i in range(2, 40)]
    res = evaluate(intervals, stage_tie_frost_heat, get_crop("wheat"))
    assert res.primary_threat == Threat.FROST.value


def test_weather_digest_computation():
    crop = get_crop("wheat")
    intervals = [
        ForecastInterval("t0", 35.0, 85.0, 45.0, 12.0),
        ForecastInterval("t1", 18.0, 85.0, 20.0, 8.0),
        ForecastInterval("t2", 20.0, 85.0, 10.0, 0.0),
        ForecastInterval("t3", 22.0, 85.0, 15.0, 0.0),
        ForecastInterval("t4", 10.0, 50.0, 5.0, 0.0),
    ]
    digest = compute_digest(intervals, crop)
    assert digest.peak_temp_c == 35.0
    assert digest.min_temp_c == 10.0
    assert digest.total_rain_mm == 20.0
    assert digest.max_wind_kmh == 45.0
    assert digest.peak_humidity_pct == 85.0
    assert digest.longest_disease_window_h == 9
