"""Game-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Nested lightweight schemas ──────────────────────────────────────────


class TagBrief(BaseModel):
    """Tag snippet embedded in game card / detail."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GameAliasBrief(BaseModel):
    id: int
    alias: str
    lang: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GameImageBrief(BaseModel):
    id: int
    url: str
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class GameResourceBrief(BaseModel):
    id: int
    resource_type: int
    title: str
    file_name: str
    file_size: int
    download_count: int = 0
    version: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Card / List schemas ─────────────────────────────────────────────────


class GameCard(BaseModel):
    """Compact card for list / grid display (TouchGal-style)."""

    id: int
    title: str
    original_title: Optional[str] = None
    cover_url: Optional[str] = None
    developer: Optional[str] = None
    release_date: Optional[date] = None
    nsfw: bool = False

    # Scores
    bgm_score: Optional[Decimal] = None
    vndb_score: Optional[Decimal] = None
    rating_avg: Decimal = Decimal("0.00")
    rating_count: int = 0

    # Counters
    view_count: int = 0
    favorite_count: int = 0
    download_count: int = 0
    comment_count: int = 0

    # Tags (top N)
    tags: list[TagBrief] = []

    model_config = ConfigDict(from_attributes=True)


class GameListResponse(BaseModel):
    """Paginated list wrapper."""

    items: list[GameCard]
    total: int
    page: int
    page_size: int


# ── Detail schema ────────────────────────────────────────────────────────


class GameDetail(BaseModel):
    """Full game detail page payload."""

    id: int
    title: str
    original_title: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    description_en: Optional[str] = None
    description_ja: Optional[str] = None
    cover_url: Optional[str] = None
    nsfw: bool = False

    developer: Optional[str] = None
    publisher: Optional[str] = None
    release_date: Optional[date] = None

    # External IDs
    bgm_id: Optional[int] = None
    bgm_score: Optional[Decimal] = None
    bgm_rank: Optional[int] = None
    vndb_id: Optional[str] = None
    vndb_score: Optional[Decimal] = None

    # Community stats
    rating_avg: Decimal = Decimal("0.00")
    rating_count: int = 0
    view_count: int = 0
    favorite_count: int = 0
    download_count: int = 0
    comment_count: int = 0

    is_favorited: bool = False

    status: int = 0

    # Relations
    aliases: list[GameAliasBrief] = []
    images: list[GameImageBrief] = []
    tags: list[TagBrief] = []
    resources: list[GameResourceBrief] = []

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Query / filter parameters ───────────────────────────────────────────


class GameSearchParams(BaseModel):
    """游戏列表/搜索的查询参数。

    status 以 int 对外暴露（API 友好），但加验证器确保只接受合法值（0-4），
    crud 层负责 int -> GameStatus 枚举的转换，不在 schema 层做 ORM 依赖。
    """

    q: Optional[str] = Field(None, description="全文搜索关键词")
    tag: Optional[str] = Field(None, description="标签名称，多个用逗号分隔")
    developer: Optional[str] = None
    nsfw: Optional[bool] = None
    year: Optional[int] = Field(None, ge=1980, le=2030)
    status: Optional[int] = Field(
        None,
        description="游戏状态: 0=草稿 1=待审 2=已发布 3=拒绝 4=归档",
    )
    sort: str = Field("latest", description="排序: latest / rating / views / downloads")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """接受 None 或 0-4 的整数，拒绝不在枚举范围内的值。"""
        if v is None:
            return v
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise ValueError("status 必须是整数")
        if v not in (0, 1, 2, 3, 4):
            raise ValueError("status 只能是 0=草稿 1=待审 2=已发布 3=拒绝 4=归档")
        return v

    @field_validator("sort", mode="before")
    @classmethod
    def validate_sort(cls, v):
        """限制排序字段防止 SQL 注入风险。"""
        allowed = {"latest", "rating", "views", "downloads"}
        if v not in allowed:
            return "latest"
        return v
