from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text, Boolean
from datetime import datetime
from backend.database import Base


class BloodReport(Base):
    """Stores parsed values from an uploaded blood test report."""
    __tablename__ = "blood_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # Raw OCR text
    raw_text = Column(Text, nullable=True)

    # Parsed CBC values
    hemoglobin = Column(Float, nullable=True)        # g/dL  normal: M 13.5-17.5, F 12-15.5
    platelets = Column(Float, nullable=True)         # lakhs/µL  normal: 1.5-4.0
    wbc = Column(Float, nullable=True)               # thousands/µL  normal: 4-11
    rbc = Column(Float, nullable=True)               # millions/µL  normal: 4.5-5.5
    hematocrit = Column(Float, nullable=True)        # %  normal: 38-50

    # Lipid panel
    total_cholesterol = Column(Float, nullable=True) # mg/dL  normal: <200
    ldl = Column(Float, nullable=True)               # mg/dL  normal: <100
    hdl = Column(Float, nullable=True)               # mg/dL  normal: >40
    triglycerides = Column(Float, nullable=True)     # mg/dL  normal: <150

    # Kidney / liver
    creatinine = Column(Float, nullable=True)        # mg/dL  normal: 0.6-1.2
    urea = Column(Float, nullable=True)              # mg/dL  normal: 7-20
    sgpt = Column(Float, nullable=True)              # U/L    normal: 7-56
    sgot = Column(Float, nullable=True)              # U/L    normal: 10-40

    # Thyroid
    tsh = Column(Float, nullable=True)               # µIU/mL normal: 0.4-4.0

    # HbA1c (3-month sugar average)
    hba1c = Column(Float, nullable=True)             # %  normal: <5.7

    # Vitamin / mineral
    vitamin_d = Column(Float, nullable=True)         # ng/mL  normal: 30-100
    vitamin_b12 = Column(Float, nullable=True)       # pg/mL  normal: 200-900
    iron = Column(Float, nullable=True)              # µg/dL  normal: 60-170

    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_latest = Column(Boolean, default=True)
