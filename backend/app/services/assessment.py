"""Cached risk assessment per plot: fetch, score, store, and serve stale when the provider is down."""

import datetime
import json
import logging
import threading
from dataclasses import asdict
from datetime import UTC

import httpx
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.domain.catalogue import CropConfig, StageConfig
from app.domain.engine import (
    AssessmentResult,
    ForecastInterval,
    InsufficientForecast,
    compute_digest,
    evaluate,
)
from app.errors import CatalogueMismatchError, UpstreamUnavailableError
from app.models import Plot, RiskAssessment
from app.services import advisory, weather
from app.services.catalogue_loader import CATALOGUE_VERSION, get_crop, get_stage

logger = logging.getLogger("croprisk")

CACHE_TTL = datetime.timedelta(hours=12)
STALE_SERVE_CAP = datetime.timedelta(hours=48)
REFRESH_COOLDOWN = datetime.timedelta(minutes=10)

# One lock per plot so two requests for the same plot don't both call the weather API.
# Only works inside one process. Re-entrant because re-scoring takes it again.
_plot_locks: dict[int, threading.RLock] = {}
_locks_mutex = threading.Lock()


def _get_plot_lock(plot_id: int) -> threading.RLock:
    with _locks_mutex:
        return _plot_locks.setdefault(plot_id, threading.RLock())


def _parse_iso(dt_str: str) -> datetime.datetime:
    dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def location_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.2f}:{longitude:.2f}"


def forecast_age(row: RiskAssessment, now: datetime.datetime) -> datetime.timedelta:
    return now - _parse_iso(row.forecast_fetched_at)


def is_row_relevant(row: RiskAssessment, plot: Plot) -> bool:
    """True when the row was scored for this plot's location, stage and catalogue."""
    return (
        row.location_key == location_key(plot.latitude, plot.longitude)
        and row.stage_id == plot.stage_id
        and row.catalogue_version == CATALOGUE_VERSION
    )


def catalogue_entry(plot: Plot) -> tuple[CropConfig, StageConfig]:
    crop = get_crop(plot.crop_id)
    stage = get_stage(plot.crop_id, plot.stage_id)
    if crop is None or stage is None:
        raise CatalogueMismatchError(
            f"Stage {plot.stage_id} is not in the crop catalogue any more. Edit the field."
        )
    return crop, stage


def _days_after_sowing(plot: Plot) -> int:
    return max(0, (datetime.date.today() - plot.sowing_date).days)


def _score(plot: Plot, intervals: list[ForecastInterval], advisory_builder):
    crop, stage = catalogue_entry(plot)
    result: AssessmentResult = evaluate(intervals, stage, crop)
    digest = compute_digest(intervals, crop)
    adv = advisory_builder(
        result, crop, stage, plot.location_name, _days_after_sowing(plot), digest
    )
    return result, adv


def _rescore(plot: Plot, row: RiskAssessment, db: Session, advisory_builder) -> RiskAssessment:
    """Score the stored forecast again for the plot's current stage. No network call.

    forecast_fetched_at and created_at stay as they are, so the forecast still ages.
    """
    intervals = [ForecastInterval(**item) for item in json.loads(row.forecast)]
    result, adv = _score(plot, intervals, advisory_builder)
    row.stage_id = plot.stage_id
    row.catalogue_version = CATALOGUE_VERSION
    row.score = result.score
    row.severity = result.severity
    row.primary_threat = result.primary_threat
    row.hazard_indices = json.dumps(result.hazard_indices)
    row.advisory = adv.model_dump_json(exclude={"source"})
    row.advisory_source = adv.source
    db.commit()
    db.refresh(row)
    return row


def cached_or_rescore(
    plot: Plot,
    row: RiskAssessment | None,
    now: datetime.datetime,
    db: Session,
    advisory_builder=None,
) -> RiskAssessment | None:
    """Return a row that is valid for the plot without calling the weather API.

    None means a new forecast is needed: no row, a different location, or a forecast older
    than the TTL. A changed stage or catalogue with a young forecast is re-scored in place.
    """
    if row is None or row.location_key != location_key(plot.latitude, plot.longitude):
        return None
    if forecast_age(row, now) >= CACHE_TTL:
        return None
    if not is_row_relevant(row, plot):
        with _get_plot_lock(plot.id):
            row = _rescore(plot, row, db, advisory_builder or advisory.build_advisory)
    return row


def _store_new_assessment(
    plot: Plot,
    intervals: list[ForecastInterval],
    now: datetime.datetime,
    db: Session,
    advisory_builder,
) -> RiskAssessment:
    result, adv = _score(plot, intervals, advisory_builder)
    now_iso = now.isoformat()
    values = {
        "location_key": location_key(plot.latitude, plot.longitude),
        "stage_id": plot.stage_id,
        "catalogue_version": CATALOGUE_VERSION,
        "score": result.score,
        "severity": result.severity,
        "primary_threat": result.primary_threat,
        "hazard_indices": json.dumps(result.hazard_indices),
        "forecast": json.dumps([asdict(i) for i in intervals]),
        "forecast_fetched_at": now_iso,
        "advisory": adv.model_dump_json(exclude={"source"}),
        "advisory_source": adv.source,
        "created_at": now_iso,
    }
    # Upsert so a second writer updates the row instead of hitting the primary key.
    stmt = sqlite_insert(RiskAssessment).values(plot_id=plot.id, **values)
    db.execute(stmt.on_conflict_do_update(index_elements=["plot_id"], set_=values))
    db.commit()
    return db.query(RiskAssessment).filter(RiskAssessment.plot_id == plot.id).one()


def build_response(plot: Plot, row: RiskAssessment, is_stale: bool, refreshed: bool) -> dict:
    crop, stage = catalogue_entry(plot)
    intervals = [ForecastInterval(**item) for item in json.loads(row.forecast)]
    digest = compute_digest(intervals, crop)
    hazard_indices = {k: round(float(v), 1) for k, v in json.loads(row.hazard_indices).items()}

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
            "days_after_sowing": _days_after_sowing(plot),
        },
        "risk": {
            "score": row.score,
            "severity": row.severity,
            "primary_threat": row.primary_threat,
            "hazard_indices": hazard_indices,
            "created_at": row.created_at,
            "forecast_fetched_at": row.forecast_fetched_at,
            "is_stale": is_stale,
        },
        "advisory": {**json.loads(row.advisory), "source": row.advisory_source},
        "weather": {
            "digest": asdict(digest),
            "intervals": [asdict(i) for i in intervals],
        },
        "refreshed": refreshed,
    }


def get_plot_risk(
    plot: Plot,
    db: Session,
    force: bool = False,
    weather_provider=None,
    advisory_builder=None,
    now: datetime.datetime | None = None,
) -> dict:
    """Serve the cached assessment, or fetch a new forecast when needed (or when forced).

    `refreshed` in the result says whether a new forecast was fetched in this call.
    """
    weather_provider = weather_provider or weather.fetch_forecast
    advisory_builder = advisory_builder or advisory.build_advisory
    now = now or datetime.datetime.now(UTC)
    catalogue_entry(plot)  # 409 before any network call

    with _get_plot_lock(plot.id):
        row = db.query(RiskAssessment).filter(RiskAssessment.plot_id == plot.id).first()

        # A forced refresh inside the cooldown just serves the cache.
        in_cooldown = row is not None and forecast_age(row, now) < REFRESH_COOLDOWN
        if not force or in_cooldown:
            cached = cached_or_rescore(plot, row, now, db, advisory_builder)
            if cached is not None:
                return build_response(plot, cached, is_stale=False, refreshed=False)

        try:
            intervals = weather_provider(plot.latitude, plot.longitude)
            new_row = _store_new_assessment(plot, intervals, now, db, advisory_builder)
            return build_response(plot, new_row, is_stale=False, refreshed=True)
        except (UpstreamUnavailableError, InsufficientForecast, httpx.HTTPError) as exc:
            db.rollback()
            logger.warning("Weather fetch failed for plot %s: %s", plot.id, exc)
            same_place = row is not None and row.location_key == location_key(
                plot.latitude, plot.longitude
            )
            if same_place and forecast_age(row, now) <= STALE_SERVE_CAP:
                if not is_row_relevant(row, plot):
                    row = _rescore(plot, row, db, advisory_builder)
                return build_response(plot, row, is_stale=True, refreshed=False)
            raise UpstreamUnavailableError(
                "Weather provider unavailable and no recent assessment is stored."
            ) from exc
        except Exception:
            db.rollback()
            raise
