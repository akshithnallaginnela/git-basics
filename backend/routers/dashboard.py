from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.health_record import VitalReading, DietEntry
from backend.models.user import User
from backend.ml.trend_analyzer import VitalTrendAnalyzer
from backend.ml.preventive_analysis import PreventiveAnalysisEngine
from backend.ml.dynamic_task_generator import DynamicTaskGenerator
from backend.ml.trained_health_model import TrainedHealthPredictor
from backend.security.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_predictor = TrainedHealthPredictor()


def _engines(db: Session):
    trend = VitalTrendAnalyzer(db)
    preventive = PreventiveAnalysisEngine(db, trend)
    tasks = DynamicTaskGenerator(db, preventive, trend)
    return trend, preventive, tasks


@router.get("/vitals-trends")
def get_vitals_trends(
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trend, _, _ = _engines(db)
    return {
        "bp_trends": trend.calculate_bp_trends(current_user.id, days),
        "glucose_trends": trend.calculate_glucose_trends(current_user.id, days),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/body-status")
def get_body_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, preventive, _ = _engines(db)
    return preventive.generate_body_status(current_user.id)


@router.get("/daily-tasks")
def get_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, _, task_gen = _engines(db)
    tasks = task_gen.generate_daily_tasks(current_user.id)
    return {"tasks": tasks, "count": len(tasks), "generated_at": datetime.utcnow().isoformat()}


@router.get("/health-risk")
def get_health_risk(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No vitals recorded yet")

    return _predictor.predict_health_risk({
        "systolic_bp": latest.systolic_bp,
        "diastolic_bp": latest.diastolic_bp,
        "blood_glucose": latest.blood_glucose,
        "weight": latest.weight,
        "age": current_user.age,
        "activity_level": current_user.activity_level,
    })


@router.get("/diet-recommendations")
def get_diet_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No vitals recorded yet")

    diet_history = db.query(DietEntry).filter(DietEntry.user_id == current_user.id).all()
    return _predictor.recommend_diet(
        {"blood_glucose": latest.blood_glucose, "systolic_bp": latest.systolic_bp, "weight": latest.weight},
        diet_history,
    )


@router.get("/analytics-dashboard")
def get_analytics_dashboard(
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trend, preventive, task_gen = _engines(db)
    latest = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id)
        .order_by(VitalReading.reading_time.desc())
        .first()
    )
    vitals_dict = {
        "systolic_bp": latest.systolic_bp if latest else None,
        "diastolic_bp": latest.diastolic_bp if latest else None,
        "blood_glucose": latest.blood_glucose if latest else None,
        "weight": latest.weight if latest else None,
        "age": current_user.age,
        "activity_level": current_user.activity_level,
    }
    return {
        "user": {"id": current_user.id, "name": current_user.name},
        "vitals_trends": {
            "bp": trend.calculate_bp_trends(current_user.id, days),
            "glucose": trend.calculate_glucose_trends(current_user.id, days),
        },
        "body_status": preventive.generate_body_status(current_user.id),
        "daily_tasks": task_gen.generate_daily_tasks(current_user.id),
        "health_risk": _predictor.predict_health_risk(vitals_dict),
        "diet_recommendations": _predictor.recommend_diet(vitals_dict),
        "generated_at": datetime.utcnow().isoformat(),
    }
