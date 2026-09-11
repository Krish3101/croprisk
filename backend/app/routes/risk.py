"""Risk routes: compute or fetch cached field risk assessment."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import NotFoundError
from app.models import Plot, User
from app.schemas import PlotRiskResponse
from app.services.assessment import get_plot_risk

router = APIRouter(prefix="/plots", tags=["risk"])


@router.get("/{plot_id}/risk", response_model=PlotRiskResponse)
def get_risk(
    plot_id: int,
    refresh: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlotRiskResponse:
    plot = (
        db.query(Plot)
        .filter(Plot.id == plot_id, Plot.user_id == current_user.id)
        .first()
    )
    if not plot:
        raise NotFoundError(f"Plot {plot_id} not found.")

    response_dict = get_plot_risk(plot, db, refresh=refresh)
    return PlotRiskResponse(**response_dict)
