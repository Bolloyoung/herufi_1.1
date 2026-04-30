from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionBase(BaseModel):
    domain: str
    subject: str
    model_name: str
    predicted_value: dict
    confidence: float
    resolves_at: datetime | None = None


class PredictionCreate(PredictionBase):
    pass


class PredictionUpdate(BaseModel):
    domain: str | None = None
    subject: str | None = None
    model_name: str | None = None
    predicted_value: dict | None = None
    confidence: float | None = None
    resolves_at: datetime | None = None


class PredictionResolve(BaseModel):
    actual_value: dict
    is_correct: bool


class PredictionOut(PredictionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predicted_at: datetime
    actual_value: dict | None
    is_correct: bool | None
    created_at: datetime


class TrackRecordStats(BaseModel):
    total: int
    resolved: int
    correct: int
    hit_rate: float
    by_domain: dict[str, dict[str, int | float]]
