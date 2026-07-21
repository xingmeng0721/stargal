"""Save-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SaveCreate(BaseModel):
    """创建存档(上传元数据，文件本体由 upload 模块处理)。"""

    game_id: int
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    storage_path: str = Field(..., max_length=500)
    file_size: int = Field(..., gt=0)
    file_hash: Optional[str] = Field(None, max_length=64)
    visibility: int = Field(0, description="0=私有(默认) 1=公开")


class SaveOut(BaseModel):
    id: int
    game_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    storage_path: str
    file_size: int
    file_hash: Optional[str] = None
    visibility: int = 0
    published_at: Optional[datetime] = None
    download_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SaveListResponse(BaseModel):
    items: list[SaveOut]
    total: int
    page: int
    page_size: int
