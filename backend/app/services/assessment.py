"""Assessment orchestration service: caching, weather integration, and degraded serving."""

import datetime
import json
import logging
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.domain.crops import get_crop, get_stage
from app.domain.engine import ForecastInterval, compute_digest, evaluate
from app.errors import NotFoundError, UpstreamUnavailableError
from app.models import Plot, RiskAssessment
from app.services import advisory, weather

logger = logging.getLogger("croprisk")


def _parse_iso(dt_str: str) -> datetime.datetime:
    # Handle ISO-8601 strings with or without Z
    cleaned = dt_str.replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    return dt


def _build_response_from_row(
    plot: Plot,
    row: RiskAssessment,
    is_stale: bool,
) -> dict:
    crop = get_crop(plot.crop_id)
    if crop is None:
        raise NotFoundError(f"Crop {plot.crop_id} not found.")
    stage = get_stage(plot.crop_id, plot.stage_id)
    if stage is None:
        raise NotFoundError(f"Stage {plot.stage_id} not found.")

    days_after_sowing = max(0, (datetime.date.today() - plot.sowing_date).days)

    raw_intervals = json.loads(row.forecast)
    intervals = [ForecastInterval(**item) for item in raw_intervals]
    digest = compute_digest(intervals, crop)

    hazard_indices = json.loads(row.hazard_indices)
    rounded_hazard_indices = {k: round(float(v), 1) for k, v in hazard_indices.items()}

    advisory_dict = json.loads(row.advisory)
    advisory_dict["source"] = row.advisory_source

    return {
        "plot": {
            "id": plot.id,
            "name": plot.name,
            "crop": crop.common_name,
            "crop_id": plot.crop_id,
            "scientific_name": crop.scientific_name,
            "stage": stage.name,
            "stage_id": plot.stage_id,
            "bbch": stage.bbch,
            "location_name": plot.location_name,
            "latitude": plot.latitude,
            "longitude": plot.longitude,
            "sowing_date": plot.sowing_date.isoformat(),
            "days_after_sowing": days_after_sowing,
        },
        "risk": {
            "score": row.score,
            "severity": row.severity,
            "primary_threat": row.primary_threat,
            "hazard_indices": rounded_hazard_indices,
            "created_at": row.created_at,
            "is_stale": is_stale,
        },
        "advisory": advisory_dict,
        "weather": {
            "digest": asdict(digest),
            "intervals": [asdict(i) for i in intervals],
        },
    }


def get_plot_risk(
    plot: Plot,
    db: Session,
    refresh: bool = False,
    weather_provider=None,
    advisory_builder=None,
) -> dict:
    """Run the risk assessment for a plot, using the cache when it is still valid.

    1. unless refresh: if a stored row is < 12 h old and row.created_at >= plot.updated_at,
       return it (is_stale=False).
    2. intervals <- weather.forecast(plot.latitude, plot.longitude) (5s timeout).
    3. on success: stage <- crops.stage, result <- engine.evaluate, advisory <- advisory.build,
       upsert row; return it (is_stale=False).
    4. on failure: if stored row has created_at >= plot.updated_at, return it (is_stale=True),
       else raise UpstreamUnavailable -> 503.
    """
    if weather_provider is None:
        weather_provider = weather.fetch_forecast
    if advisory_builder is None:
        advisory_builder = advisory.build_advisory
    stored_row = (
        db.query(RiskAssessment).filter(RiskAssessment.plot_id == plot.id).first()
    )

    now = datetime.datetime.now(datetime.UTC)
    plot_updated_dt = _parse_iso(plot.updated_at)

    # 1. Fresh cache hit check
    if not refresh and stored_row is not None:
        row_created_dt = _parse_iso(stored_row.created_at)
        is_young = (now - row_created_dt) < datetime.timedelta(hours=12)
        is_relevant = row_created_dt >= plot_updated_dt

        if is_young and is_relevant:
            return _build_response_from_row(plot, stored_row, is_stale=False)

    # 2 & 3. Weather fetch & recompute
    try:
        intervals = weather_provider(plot.latitude, plot.longitude)
        crop = get_crop(plot.crop_id)
        if crop is None:
            raise NotFoundError(f"Crop {plot.crop_id} not found.")
        stage = get_stage(plot.crop_id, plot.stage_id)
        if stage is None:
            raise NotFoundError(f"Stage {plot.stage_id} not found.")

        result = evaluate(intervals, stage, crop)
        digest = compute_digest(intervals, crop)
        days_after_sowing = max(0, (datetime.date.today() - plot.sowing_date).days)
        advisory_res = advisory_builder(
            result, crop, stage, plot.location_name, days_after_sowing, digest
        )

        now_iso = now.isoformat()
        intervals_json = json.dumps([asdict(i) for i in intervals])
        hazard_json = json.dumps(result.hazard_indices)
        advisory_json = advisory_res.model_dump_json()

        if stored_row is None:
            stored_row = RiskAssessment(
                plot_id=plot.id,
                score=result.score,
                severity=result.severity,
                primary_threat=result.primary_threat,
                hazard_indices=hazard_json,
                forecast=intervals_json,
                advisory=advisory_json,
                advisory_source=advisory_res.source,
                created_at=now_iso,
            )
            db.add(stored_row)
        else:
            stored_row.score = result.score
            stored_row.severity = result.severity
            stored_row.primary_threat = result.primary_threat
            stored_row.hazard_indices = hazard_json
            stored_row.forecast = intervals_json
            stored_row.advisory = advisory_json
            stored_row.advisory_source = advisory_res.source
            stored_row.created_at = now_iso

        db.commit()
        db.refresh(stored_row)
        return _build_response_from_row(plot, stored_row, is_stale=False)

    except Exception as exc:
        logger.warning("Weather fetch or assessment calculation failed: %s", exc)
        # 4. Degraded serving check
        if stored_row is not None:
            row_created_dt = _parse_iso(stored_row.created_at)
            if row_created_dt >= plot_updated_dt:
                return _build_response_from_row(plot, stored_row, is_stale=True)

        raise UpstreamUnavailableError(
            "Weather provider unavailable and no valid stored assessment exists."
        ) from exc
