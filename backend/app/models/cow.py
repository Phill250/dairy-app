import enum
import uuid
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, func
from app.core.types import GUID
from app.core.database import Base


class BreedType(str, enum.Enum):
    holstein_friesian = "holstein_friesian"
    ankole = "ankole"
    ankole_friesian_cross = "ankole_friesian_cross"
    other = "other"


class CowModel(Base):
    __tablename__ = "cows"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    farmer_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    breed = Column(Enum(BreedType), nullable=False, default=BreedType.other)
    created_at = Column(DateTime(timezone=True), server_default=func.now())