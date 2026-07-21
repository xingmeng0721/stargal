"""Tag-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TagOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    usage_count: int = 0
    category_name: Optional[str] = None
    category_type: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TagCategoryOut(BaseModel):
    id: int
    name: str
    type: int = 3
    sort_order: int = 0
    tags: list[TagOut] = []

    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    items: list[TagOut]
    total: int
