import uuid
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

DateStr = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
Liters = Annotated[float, Field(ge=0, le=100)]


class LogCreate(BaseModel):
    cow_id: uuid.UUID
    date: DateStr
    feed: float = Field(gt=0, le=100, description="Feed given in kg")
    milkingTimes: int = Field(gt=0, le=10)
    milkings: list[Liters] = Field(min_length=1, max_length=10)


class LogUpdate(BaseModel):
    cow_id: uuid.UUID | None = None
    date: DateStr | None = None
    feed: float | None = Field(default=None, gt=0, le=100)
    milkingTimes: int | None = Field(default=None, gt=0, le=10)
    milkings: list[Liters] | None = Field(default=None, min_length=1, max_length=10)


class LogRead(BaseModel):
    id: uuid.UUID
    cow_id: uuid.UUID
    date: str
    feed: float
    milking_times: int
    total_milk: float
    status: str
    color: str
    advice: str
    predicted_yield: float | None = None
    used_ml_model: bool = False
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PredictionRequest(BaseModel):
    cow_id: uuid.UUID
    feed: float = Field(gt=0, le=100)
    milking_times: int = Field(gt=0, le=10)


class PredictionResponse(BaseModel):
    expected_yield: float
    model_used: bool
    model_config = ConfigDict(protected_namespaces=())