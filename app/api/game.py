"""Game browsing & search API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.game import GameListResponse, GameDetail
from app.services.game import list_games, get_game_detail

router = APIRouter(prefix="/games", tags=["游戏模块"])


@router.get("", response_model=GameListResponse, summary="游戏列表")
async def game_list(
    q: Optional[str] = Query(None, description="搜索关键词"),
    tag: Optional[str] = Query(None, description="标签名，多个用逗号分隔"),
    developer: Optional[str] = Query(None, description="开发商"),
    nsfw: Optional[bool] = Query(None, description="是否包含 NSFW"),
    year: Optional[int] = Query(None, ge=1980, le=2030, description="发售年份"),
    sort: str = Query("latest", description="排序: latest/rating/views/downloads"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    获取游戏列表（卡片式），支持：
    - 关键词搜索（标题/原名/别名模糊匹配）
    - 标签筛选（AND 语义，多个标签取交集）
    - 开发商筛选
    - NSFW 过滤
    - 年份筛选
    - 排序（最新 / 评分 / 浏览 / 下载）
    - 分页
    """
    return await list_games(
        db,
        q=q,
        tag=tag,
        developer=developer,
        nsfw=nsfw,
        year=year,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/{game_id}", response_model=GameDetail, summary="游戏详情")
async def game_detail(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    获取单个游戏的完整信息，包括：
    - 基础元数据（标题、原名、简介、封面、开发商等）
    - 外部数据（BGM 评分/排名、VNDB 评分）
    - 别名列表
    - 截图列表
    - 标签列表
    - 可下载资源列表
    - 浏览量自动 +1
    """
    user_id = current_user.id if current_user else None
    detail = await get_game_detail(db, game_id, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="游戏不存在或已下架")
    return detail
