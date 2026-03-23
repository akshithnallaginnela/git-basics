from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models.health_record import VitalReading

router = APIRouter(prefix="/api/vitals", tags=["vitals"])


class VitalLogRequest(BaseModel):
    user_id: int
    systolic_bp: Optional[int] = Field(None, ge=60, le=250)
    diastolic_bp: Optional[int] = Field(None, ge=40, le=150)
    blood_glucose: Optional[float] = Field(None, ge=20, le=600)
    pulse: Optional[int] = Field(None, ge=30, le=250)
    weight: Optional[float] = Field(None, ge=20, le=300)
    height: Optional[float] = Field(None, ge=50, le=250)
    notes: Optional[str] = None
    measurement_method: str = "manual"


@router.post("/log", status_code=201)
async def log_vitals(payload: VitalLogRequest, db: Session = Depends(get_db)):
    reading = VitalReading(
        user_id=payload.user_id,
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


@router.get("/history/{user_id}")
async def get_vitals_history(user_id: int, limit: int = 30, db: Session = Depends(get_db)):
    readings = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == user_id)
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
