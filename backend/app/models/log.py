import uuid
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, func
from app.core.types import GUID
from app.core.database import Base


class LogModel(Base):
    __tablename__ = "logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    cow_id = Column(GUID(), ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String, nullable=False, index=True)
    feed = Column(Float, nullable=False)
    milking_times = Column(Integer, nullable=False)
    total_milk = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    color = Column(String, nullable=False)
    advice = Column(String, nullable=False)
    predicted_yield = Column(Float, nullable=True)
    used_ml_model = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())