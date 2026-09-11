"""Plot management routes: list, create, partial update, and delete."""

import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.domain.crops import get_crop, get_stage
from app.errors import NotFoundError, ValidationError
from app.models import Plot, RiskAssessment, User
from app.schemas import (
    CropRef,
    LatestRiskSummary,
    PlotCreateRequest,
    PlotSummary,
    PlotUpdateRequest,
    StageRef,
)

router = APIRouter(prefix="/plots", tags=["plots"])


def _to_plot_summary(plot: Plot, risk: RiskAssessment | None) -> PlotSummary:
    crop = get_crop(plot.crop_id)
    crop_name = crop.common_name if crop else plot.crop_id
    stage = get_stage(plot.crop_id, plot.stage_id)
    stage_name = stage.name if stage else plot.stage_id
    bbch = stage.bbch if stage else ""

    days_after_sowing = max(0, (datetime.date.today() - plot.sowing_date).days)

    latest_risk = None
    if risk is not None:
        latest_risk = LatestRiskSummary(
            score=risk.score,
            severity=risk.severity,
            primary_threat=risk.primary_threat,
            created_at=risk.created_at,
            is_stale=False,
        )

    return PlotSummary(
        id=plot.id,
        name=plot.name,
        crop=CropRef(id=plot.crop_id, common_name=crop_name),
        stage=StageRef(id=plot.stage_id, name=stage_name, bbch=bbch),
        location_name=plot.location_name,
        latitude=plot.latitude,
        longitude=plot.longitude,
        sowing_date=plot.sowing_date.isoformat(),
        days_after_sowing=days_after_sowing,
        latest_risk=latest_risk,
    )


@router.get("", response_model=list[PlotSummary])
def list_plots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlotSummary]:
    # Single joined query, ordered by score descending (nulls last), then by name
    results = (
        db.query(Plot, RiskAssessment)
        .outerjoin(RiskAssessment, Plot.id == RiskAssessment.plot_id)
        .filter(Plot.user_id == current_user.id)
        .order_by(
            RiskAssessment.score.desc().nullslast(),
            Plot.name.asc(),
        )
        .all()
    )

    return [_to_plot_summary(plot, risk) for plot, risk in results]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlotSummary)
def create_plot(
    req: PlotCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlotSummary:
    crop = get_crop(req.crop_id)
    if not crop:
        raise ValidationError(
            "Selected crop does not exist.",
            fields={"crop_id": "Selected crop does not exist."},
        )

    stage = get_stage(req.crop_id, req.stage_id)
    if not stage:
        raise ValidationError(
            "Selected stage does not belong to the crop.",
            fields={"stage_id": "Selected stage does not belong to the crop."},
        )

    now_iso = datetime.datetime.now(datetime.UTC).isoformat()
    plot = Plot(
        user_id=current_user.id,
        name=req.name,
        crop_id=req.crop_id,
        stage_id=req.stage_id,
        location_name=req.location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        sowing_date=req.sowing_date,
        created_at=now_iso,
        updated_at=now_iso,
    )
    db.add(plot)
    db.commit()
    db.refresh(plot)

    return _to_plot_summary(plot, None)


@router.patch("/{plot_id}", response_model=PlotSummary)
def update_plot(
    plot_id: int,
    req: PlotUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlotSummary:
    plot = (
        db.query(Plot)
        .filter(Plot.id == plot_id, Plot.user_id == current_user.id)
        .first()
    )
    if not plot:
        raise NotFoundError(f"Plot {plot_id} not found.")

    target_crop_id = req.crop_id if req.crop_id is not None else plot.crop_id
    target_stage_id = req.stage_id if req.stage_id is not None else plot.stage_id

    crop = get_crop(target_crop_id)
    if not crop:
        raise ValidationError(
            "Selected crop does not exist.",
            fields={"crop_id": "Selected crop does not exist."},
        )

    stage = get_stage(target_crop_id, target_stage_id)
    if not stage:
        raise ValidationError(
            "Selected stage does not belong to the crop.",
            fields={"stage_id": "Selected stage does not belong to the crop."},
        )

    if req.name is not None:
        plot.name = req.name
    if req.crop_id is not None:
        plot.crop_id = req.crop_id
    if req.stage_id is not None:
        plot.stage_id = req.stage_id
    if req.location_name is not None:
        plot.location_name = req.location_name
    if req.latitude is not None:
        plot.latitude = req.latitude
    if req.longitude is not None:
        plot.longitude = req.longitude
    if req.sowing_date is not None:
        plot.sowing_date = req.sowing_date

    # Bump updated_at (invalidates cached assessment)
    plot.updated_at = datetime.datetime.now(datetime.UTC).isoformat()
    db.commit()
    db.refresh(plot)

    risk = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.plot_id == plot.id)
        .first()
    )
    return _to_plot_summary(plot, risk)


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(
    plot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    plot = (
        db.query(Plot)
        .filter(Plot.id == plot_id, Plot.user_id == current_user.id)
        .first()
    )
    if not plot:
        raise NotFoundError(f"Plot {plot_id} not found.")

    db.delete(plot)
    db.commit()
