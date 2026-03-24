from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models.health_record import VitalReading
from backend.models.user import User
from backend.security.auth import get_current_user

router = APIRouter(prefix="/api/vitals", tags=["vitals"])


class VitalLogRequest(BaseModel):
    systolic_bp: Optional[int] = Field(None, ge=60, le=250)
    diastolic_bp: Optional[int] = Field(None, ge=40, le=150)
    blood_glucose: Optional[float] = Field(None, ge=20, le=600)
    pulse: Optional[int] = Field(None, ge=30, le=250)
    weight: Optional[float] = Field(None, ge=20, le=300)
    height: Optional[float] = Field(None, ge=50, le=250)
    notes: Optional[str] = None
    measurement_method: str = "manual"


@router.post("/log", status_code=201)
def log_vitals(
    payload: VitalLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reading = VitalReading(
        user_id=current_user.id,
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        blood_glucose=payload.blood_glucose,
        pulse=payload.pulse,
        weight=payload.weight,
        height=payload.height,
        notes=payload.notes,
        measurement_method=payload.measurement_method,
        reading_time=datetime.utcnow(),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return {"id": reading.id, "recorded_at": reading.reading_time.isoformat()}


@router.get("/history")
def get_vitals_history(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    readings = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id)
        .order_by(VitalReading.reading_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "systolic_bp": r.systolic_bp,
            "diastolic_bp": r.diastolic_bp,
            "blood_glucose": r.blood_glucose,
            "pulse": r.pulse,
            "weight": r.weight,
            "reading_time": r.reading_time.isoformat(),
        }
        for r in readings
    ]
