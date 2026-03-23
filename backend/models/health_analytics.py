from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Date
from datetime import datetime
from backend.database import Base


class VitalTrend(Base):
    __tablename__ = "vital_trends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    vital_type = Column(String(30), nullable=False)   # bp_systolic|bp_diastolic|glucose|weight
    period = Column(String(10), nullable=False)        # daily|weekly|monthly

    avg_value = Column(Float, nullable=False)
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    std_deviation = Column(Float, nullable=False)
    trend_direction = Column(String(15), nullable=False)  # stable|increasing|decreasing
    velocity = Column(Float, nullable=False)               # rate of change per day
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    data_points_count = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HealthAlert(Base):
    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    alert_type = Column(String(30), nullable=False)   # bp_high|glucose_high|weight_gain|anomaly|trend_warning
    severity = Column(String(10), nullable=False)      # low|medium|high|critical
    vital_type = Column(String(30), nullable=False)
    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(String(255), nullable=False)
    recommended_action = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class HabitConsistency(Base):
    __tablename__ = "habit_consistency"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    habit_type = Column(String(30), nullable=False)  # app_engagement|vitals_logging|task_completion|exercise

    logins_this_week = Column(Integer, default=0)
    avg_session_duration_minutes = Column(Float, default=0.0)
    vitals_logged_this_week = Column(Integer, default=0)
    tasks_completed_this_week = Column(Integer, default=0)
    consistency_score = Column(Float, default=0.0)  # 0-100

    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
