from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.database import Plot, RiskAssessment, User, get_db
from models.schemas import PlotCreate, PlotResponse, PlotUpdate, PlotWithRiskResponse
from services.weather_service import geocode_location
from utils.helpers import get_current_user, get_owned_plot

router = APIRouter(prefix="/api/plots", tags=["Plots"])


def _ensure_utc(dt):
    return dt.replace(tzinfo=UTC) if dt and dt.tzinfo is None else dt


@router.get("", response_model=list[PlotWithRiskResponse])
def get_plots(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plots = (
        db.query(Plot).filter(Plot.user_id == current_user.id).order_by(desc(Plot.created_at)).all()
    )
    results = []
    for p in plots:
        latest_risk = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.plot_id == p.id)
            .order_by(desc(RiskAssessment.created_at))
            .first()
        )
        if latest_risk and _ensure_utc(latest_risk.created_at) < _ensure_utc(p.updated_at):
            latest_risk = None

        p_dict = {
            "id": p.id,
            "name": p.name,
            "crop_type": p.crop_type,
            "location": p.location,
            "growth_stage": p.growth_stage,
            "sowing_date": p.sowing_date,
            "created_at": p.created_at,
            "latest_risk": latest_risk,
        }
        results.append(p_dict)

    def get_risk_score(p):
        if not p["latest_risk"]:
            return 0
        sev = p["latest_risk"].severity
        if sev == "HIGH":
            return 3
        if sev == "MODERATE":
            return 2
        if sev == "LOW":
            return 1
        return 0

    results.sort(key=get_risk_score, reverse=True)
    return results

@router.post("", response_model=PlotResponse)
async def create_plot(
    plot: PlotCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    geo_results = await geocode_location(plot.location)
    if len(geo_results) == 0:
        raise HTTPException(status_code=400, detail="Location not found.")
    if len(geo_results) > 1:
        # Prompt for clarification if ambiguous
        # Let's say if exact match by state, or just strictly reject > 1
        raise HTTPException(status_code=400, detail=f"Location is ambiguous. Found {len(geo_results)} matches. Please provide a more specific location (e.g., 'City, State, Country').")

    lat = geo_results[0]["lat"]
    lon = geo_results[0]["lon"]

    new_plot = Plot(**plot.model_dump(), lat=lat, lon=lon, user_id=current_user.id)
    db.add(new_plot)
    db.commit()
    db.refresh(new_plot)
    return new_plot


@router.patch("/{plot_id}", response_model=PlotResponse)
async def update_plot(
    plot_id: int,
    plot_update: PlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_plot = get_owned_plot(plot_id, db, current_user)

    update_data = plot_update.model_dump(exclude_unset=True)
    if "location" in update_data:
        geo_results = await geocode_location(update_data["location"])
        if len(geo_results) == 0:
            raise HTTPException(status_code=400, detail="Location not found.")
        if len(geo_results) > 1:
            raise HTTPException(status_code=400, detail=f"Location is ambiguous. Found {len(geo_results)} matches.")
        update_data["lat"] = geo_results[0]["lat"]
        update_data["lon"] = geo_results[0]["lon"]

    for key, value in update_data.items():
        setattr(db_plot, key, value)

    db.commit()
    db.refresh(db_plot)
    return db_plot


@router.delete("/{plot_id}")
def delete_plot(
    plot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    db_plot = get_owned_plot(plot_id, db, current_user)
    db.delete(db_plot)
    db.commit()
    return {"status": "success", "message": "Plot deleted"}
