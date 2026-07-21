"""Upload-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UploadInitCreate(BaseModel):
    """初始化分块上传任务。"""

    target_type: int = Field(..., description="0=游戏资源 1=存档")
    game_id: Optional[int] = None
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    file_hash: str = Field(..., min_length=64, max_length=64)
    total_chunks: int = Field(..., ge=1)


class UploadTaskOut(BaseModel):
    id: int
    upload_id: str
    user_id: int
    target_type: int
    game_id: Optional[int] = None
    file_name: str
    file_size: int
    file_hash: str
    total_chunks: int
    uploaded_chunks: int = 0
    status: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkUploadResponse(BaseModel):
    chunk_index: int
    chunk_hash: Optional[str] = None
    message: str = "分块上传成功"


class InstantUploadResponse(BaseModel):
    """秒传响应：文件已存在，无需再传。"""

    exists: bool = True
    message: str = "文件已存在，秒传成功"
    resource_id: Optional[int] = None
