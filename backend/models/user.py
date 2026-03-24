from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    activity_level = Column(Integer, default=2)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
