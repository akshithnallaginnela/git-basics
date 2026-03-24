from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.health_record import VitalReading
from backend.models.blood_report import BloodReport
from backend.models.user import User
from backend.ml.trend_analyzer import VitalTrendAnalyzer
from backend.ml.future_preventive_engine import FuturePreventiveEngine
from backend.ml.task_engine import TaskEngine
from backend.security.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_preventive = FuturePreventiveEngine()
_task_engine = TaskEngine()


def _latest_vitals(user_id: int, db: Session):
    r = db.query(VitalReading).filter(VitalReading.user_id == user_id).order_by(VitalReading.reading_time.desc()).first()
    if not r:
        return None
    return {"systolic_bp": r.systolic_bp, "diastolic_bp": r.diastolic_bp, "blood_glucose": r.blood_glucose, "weight": r.weight, "height": r.height}


def _latest_report(user_id: int, db: Session):
    r = db.query(BloodReport).filter(BloodReport.user_id == user_id, BloodReport.is_latest == True).first()
    if not r:
        return None
    return {k: getattr(r, k) for k in ["hemoglobin", "platelets", "wbc", "total_cholesterol", "ldl", "hdl", "triglycerides", "creatinine", "hba1c", "tsh", "vitamin_d", "vitamin_b12", "iron"] if getattr(r, k) is not None}


def _bmi(vitals):
    if not vitals:
        return None
    w, h = vitals.get("weight"), vitals.get("height")
    if w and h and h > 0:
        return round(w / ((h / 100) ** 2), 1)
    return None


@router.get("/analytics-dashboard")
def get_analytics_dashboard(
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trend_analyzer = VitalTrendAnalyzer(db)
    vitals = _latest_vitals(current_user.id, db)
    report = _latest_report(current_user.id, db)
    bmi = _bmi(vitals)

    bp_trend = trend_analyzer.calculate_bp_trends(current_user.id, days)
    glucose_trend = trend_analyzer.calculate_glucose_trends(current_user.id, days)
    vitals_trend = {"bp": bp_trend, "glucose": glucose_trend}

    preventive = _preventive.generate(vitals_trend, vitals or {}, report)
    tasks = _task_engine.generate(vitals, vitals_trend, report, bmi)

    # Last 7 readings for chart
    readings = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id)
        .order_by(VitalReading.reading_time.desc())
        .limit(7)
        .all()
    )
    chart_data = [
        {"date": r.reading_time.strftime("%a"), "systolic": r.systolic_bp, "diastolic": r.diastolic_bp, "glucose": r.blood_glucose}
        for r in reversed(readings)
    ]

    return {
        "user": {"id": current_user.id, "name": current_user.name},
        "latest_vitals": vitals,
        "bmi": bmi,
        "vitals_trend": vitals_trend,
        "chart_data": chart_data,
        "preventive_care": preventive,   # future predictions
        "daily_tasks": tasks,            # present-day actions
        "blood_report": report,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/preventive-care")
def get_preventive_care(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trend_analyzer = VitalTrendAnalyzer(db)
    vitals = _latest_vitals(current_user.id, db)
    report = _latest_report(current_user.id, db)
    vitals_trend = {
        "bp": trend_analyzer.calculate_bp_trends(current_user.id),
        "glucose": trend_analyzer.calculate_glucose_trends(current_user.id),
    }
    return _preventive.generate(vitals_trend, vitals or {}, report)


@router.get("/daily-tasks")
def get_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trend_analyzer = VitalTrendAnalyzer(db)
    vitals = _latest_vitals(current_user.id, db)
    report = _latest_report(current_user.id, db)
    bmi = _bmi(vitals)
    vitals_trend = {
        "bp": trend_analyzer.calculate_bp_trends(current_user.id),
        "glucose": trend_analyzer.calculate_glucose_trends(current_user.id),
    }
    tasks = _task_engine.generate(vitals, vitals_trend, report, bmi)
    return {"tasks": tasks, "count": len(tasks), "generated_at": datetime.utcnow().isoformat()}
