from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from datetime import datetime
from backend.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(30), nullable=False)   # vitals|exercise|diet|wellness
    priority = Column(String(10), default="medium") # low|medium|high|urgent
    points = Column(Integer, default=10)
    is_dynamic = Column(Boolean, default=False)     # auto-generated vs static
    triggered_by = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
