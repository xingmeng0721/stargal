"""Play / rating schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    score: Decimal = Field(..., ge=0, le=10, decimal_places=2)


class RatingOut(BaseModel):
    id: int
    user_id: int
    game_id: int
    score: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserGameStatusCreate(BaseModel):
    status: int = Field(
        ..., description="0=想玩 1=在玩 2=已完 3=搁置 4=弃坑"
    )


class UserGameStatusOut(BaseModel):
    id: int
    user_id: int
    game_id: int
    status: int
    total_minutes: int = 0
    last_played_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
