from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.database import get_db, User, Plot, RiskAssessment
from models.schemas import RiskAssessmentResponse
from utils.helpers import get_current_user
from services.risk_engine import generate_risk_assessment
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/plots", tags=["Risk Assessment"])

@router.get("/{plot_id}/risk", response_model=RiskAssessmentResponse)
async def get_plot_risk(plot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
        
    latest_assessment = db.query(RiskAssessment).filter(RiskAssessment.plot_id == plot_id).order_by(desc(RiskAssessment.created_at)).first()
    
    # Check if we need to generate a new assessment (older than 12 hours)
    if not latest_assessment or datetime.utcnow() - latest_assessment.created_at > timedelta(hours=12):
        try:
            risk_data = await generate_risk_assessment(plot.crop_type, plot.growth_stage, plot.location)
            new_assessment = RiskAssessment(
                plot_id=plot.id,
                risk_score=risk_data["risk_score"],
                severity=risk_data["severity"],
                primary_risk=risk_data["primary_risk"],
                analysis=risk_data["analysis"],
                recommendation=risk_data["recommendation"],
                weather_summary=risk_data.get("weather_summary", "")
            )
            db.add(new_assessment)
            db.commit()
            db.refresh(new_assessment)
            return new_assessment
        except HTTPException as e:
            # If API fails and we have a stale assessment, return it. Otherwise, bubble error.
            if latest_assessment:
                return latest_assessment
            raise e
            
    return latest_assessment
