from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccuracyRequest(BaseModel):
    start: str = Field(..., description="Start date")
    end: str = Field(..., description="Exclusive end date")


class AccuracyMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matched_intervals: int
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
