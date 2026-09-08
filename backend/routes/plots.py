from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.database import Plot, RiskAssessment, User, get_db
from models.schemas import PlotCreate, PlotResponse, PlotUpdate, PlotWithRiskResponse
from utils.helpers import get_current_user, get_owned_plot

router = APIRouter(prefix="/api/plots", tags=["Plots"])


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
    return results


@router.post("", response_model=PlotResponse)
def create_plot(
    plot: PlotCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    new_plot = Plot(**plot.model_dump(), user_id=current_user.id)
    db.add(new_plot)
    db.commit()
    db.refresh(new_plot)
    return new_plot


@router.patch("/{plot_id}", response_model=PlotResponse)
def update_plot(
    plot_id: int,
    plot_update: PlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_plot = get_owned_plot(plot_id, db, current_user)

    update_data = plot_update.model_dump(exclude_unset=True)
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
