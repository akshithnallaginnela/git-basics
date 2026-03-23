from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.health_record import VitalReading, DietEntry
from backend.ml.trend_analyzer import VitalTrendAnalyzer
from backend.ml.preventive_analysis import PreventiveAnalysisEngine
from backend.ml.dynamic_task_generator import DynamicTaskGenerator
from backend.ml.trained_health_model import TrainedHealthPredictor

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Singleton predictor (model loaded once at startup)
_predictor = TrainedHealthPredictor()


def _get_engines(db: Session):
    """Build ML engine chain for a request-scoped DB session."""
    trend = VitalTrendAnalyzer(db)
    preventive = PreventiveAnalysisEngine(db, trend)
    tasks = DynamicTaskGenerator(db, preventive, trend)
    return trend, preventive, tasks


@router.get("/vitals-trends")
async def get_vitals_trends(
    days: int = Query(default=30, ge=7, le=365),
    user_id: int = Query(..., description="Authenticated user ID"),
    db: Session = Depends(get_db),
):
    trend, _, _ = _get_engines(db)
    return {
        "bp_trends": trend.calculate_bp_trends(user_id, days),
        "glucose_trends": trend.calculate_glucose_trends(user_id, days),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/body-status")
async def get_body_status(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    _, preventive, _ = _get_engines(db)
    return preventive.generate_body_status(user_id)


@router.get("/daily-tasks")
async def get_daily_tasks(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    _, _, task_gen = _get_engines(db)
    tasks = task_gen.generate_daily_tasks(user_id)
    return {"tasks": tasks, "count": len(tasks), "generated_at": datetime.utcnow().isoformat()}


@router.get("/health-risk")
async def get_health_risk(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == user_id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No vitals recorded for this user")

    vitals_dict = {
        "systolic_bp": latest.systolic_bp,
        "diastolic_bp": latest.diastolic_bp,
        "blood_glucose": latest.blood_glucose,
        "weight": latest.weight,
    }
    return _predictor.predict_health_risk(vitals_dict)


@router.get("/diet-recommendations")
async def get_diet_recommendations(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == user_id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No vitals recorded for this user")

    vitals_dict = {
        "blood_glucose": latest.blood_glucose,
        "systolic_bp": latest.systolic_bp,
        "weight": latest.weight,
    }
    diet_history = db.query(DietEntry).filter(DietEntry.user_id == user_id).all()
    return _predictor.recommend_diet(vitals_dict, diet_history)


@router.get("/analytics-dashboard")
async def get_analytics_dashboard(
    user_id: int = Query(...),
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Single consolidated endpoint — all analytics in one call."""
    trend, preventive, task_gen = _get_engines(db)

    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == user_id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    vitals_dict = {
        "systolic_bp": latest.systolic_bp if latest else None,
        "diastolic_bp": latest.diastolic_bp if latest else None,
        "blood_glucose": latest.blood_glucose if latest else None,
        "weight": latest.weight if latest else None,
    }

    return {
        "vitals_trends": {
            "bp": trend.calculate_bp_trends(user_id, days),
            "glucose": trend.calculate_glucose_trends(user_id, days),
        },
        "body_status": preventive.generate_body_status(user_id),
        "daily_tasks": task_gen.generate_daily_tasks(user_id),
        "health_risk": _predictor.predict_health_risk(vitals_dict),
        "diet_recommendations": _predictor.recommend_diet(vitals_dict),
        "generated_at": datetime.utcnow().isoformat(),
    }
