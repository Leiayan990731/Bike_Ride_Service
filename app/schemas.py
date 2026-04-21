import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field, validator


class RideStartRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    bike_id: str = Field(..., min_length=1, max_length=128)


class RideEndRequest(BaseModel):
    ride_id: int = Field(..., gt=0)


class RideResponse(BaseModel):
    id: int
    user_id: str
    bike_id: str
    started_at: dt.datetime
    ended_at: Optional[dt.datetime]

    class Config:
        orm_mode = True


class RideCostResponse(BaseModel):
    ride_id: int
    currency: str = "HKD"
    cost: float = Field(..., ge=0, description="Total cost in HKD")
    duration_seconds: int = Field(..., ge=0)
    started_at: dt.datetime
    ended_at: dt.datetime

    @validator("ended_at")
    def _ended_after_started(cls, v, values):
        started = values.get("started_at")
        if started and v < started:
            raise ValueError("ended_at must be >= started_at")
        return v
