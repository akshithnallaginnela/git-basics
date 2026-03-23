from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from backend.database import Base


class VitalReading(Base):
    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    reading_time = Column(DateTime, default=datetime.utcnow, index=True)
    recorded_at_timezone = Column(String(50), default="UTC")
    data_quality_score = Column(Float, default=1.0)
    measurement_method = Column(String(20), default="manual")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DietEntry(Base):
    __tablename__ = "diet_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast|lunch|dinner|snack
    food_items = Column(Text, nullable=False)        # JSON array stored as text
    estimated_calories = Column(Integer, nullable=True)
    macros = Column(Text, nullable=True)             # JSON {protein, carbs, fat}
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginEvent(Base):
    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow, index=True)
    session_duration_minutes = Column(Integer, default=0)
    tasks_completed_in_session = Column(Integer, default=0)
    vitals_logged_in_session = Column(Integer, default=0)


class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow, index=True)
    completion_time_minutes = Column(Integer, default=0)
    user_notes = Column(Text, nullable=True)
