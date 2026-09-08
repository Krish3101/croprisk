from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.database import RiskAssessment, User, get_db
from models.schemas import RiskAssessmentResponse
from services.risk_engine import generate_risk_assessment
from utils.helpers import get_current_user, get_owned_plot

router = APIRouter(prefix="/api/plots", tags=["Risk Assessment"])


@router.get("/{plot_id}/risk", response_model=RiskAssessmentResponse)
async def get_plot_risk(
    plot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    plot = get_owned_plot(plot_id, db, current_user)

    latest_assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.plot_id == plot_id)
        .order_by(desc(RiskAssessment.created_at))
        .first()
    )

    # Check if we need to generate a new assessment (older than 12 hours or plot was updated)
    def ensure_utc(dt):
        return dt.replace(tzinfo=UTC) if dt and dt.tzinfo is None else dt

    if not latest_assessment or ensure_utc(datetime.now(UTC)) - ensure_utc(latest_assessment.created_at) > timedelta(hours=12) or ensure_utc(latest_assessment.created_at) < ensure_utc(plot.updated_at):
        try:
            risk_data = await generate_risk_assessment(
                plot.crop_type, plot.growth_stage, plot.lat, plot.lon
            )
            new_assessment = RiskAssessment(
                plot_id=plot.id,
                risk_score=risk_data["risk_score"],
                severity=risk_data["severity"],
                primary_risk=risk_data["primary_risk"],
                analysis=risk_data["analysis"],
                recommendation=risk_data["recommendation"],
                weather_summary=risk_data.get("weather_summary", ""),
            )
            db.add(new_assessment)
            db.commit()
            db.refresh(new_assessment)
            return new_assessment
        except HTTPException as e:
            # If API fails and we have a stale assessment, return it. Otherwise, bubble error.
            if latest_assessment and ensure_utc(latest_assessment.created_at) >= ensure_utc(plot.updated_at):
                latest_assessment.is_stale = True
                return latest_assessment
            raise e

    # If it is valid and within freshness window
    latest_assessment.is_stale = False
    return latest_assessment
