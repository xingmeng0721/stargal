"""Interaction schemas – comments, favorites, likes."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.game import GameCard


# ── Comment ──────────────────────────────────────────────────────────────


class CommentUserBrief(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = Field(None, description="父评论 ID，用于回复")


class CommentOut(BaseModel):
    id: int
    user: Optional[CommentUserBrief] = None
    game_id: int
    parent_id: Optional[int] = None
    content: str
    like_count: int = 0
    reply_count: int = 0
    replies: list["CommentOut"] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    items: list[CommentOut]
    total: int
    page: int
    page_size: int


# ── Favorite ─────────────────────────────────────────────────────────────


class FavoriteCreate(BaseModel):
    game_id: int
    folder: Optional[str] = Field(None, max_length=50)


class FavoriteOut(BaseModel):
    id: int
    game: Optional[GameCard] = None
    folder: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteListResponse(BaseModel):
    items: list[FavoriteOut]
    total: int
    page: int
    page_size: int


# ── Like ─────────────────────────────────────────────────────────────────


class LikeCreate(BaseModel):
    target_type: int = Field(..., description="0=游戏 1=评论")
    target_id: int


class LikeOut(BaseModel):
    id: int
    target_type: int
    target_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
