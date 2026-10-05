import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.cow import BreedType


class CowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    breed: BreedType = BreedType.other


class CowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    breed: BreedType | None = None


class CowRead(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    name: str
    breed: BreedType
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)