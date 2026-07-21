"""Play API endpoints – ratings and play status."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.play import (
    RatingCreate,
    RatingOut,
    UserGameStatusCreate,
    UserGameStatusOut,
)
from app.services.play import (
    set_rating,
    get_user_rating,
    set_play_status,
    get_play_status,
)

router = APIRouter(prefix="/games", tags=["游玩模块"])


@router.post(
    "/{game_id}/rating",
    response_model=RatingOut,
    summary="评分游戏",
)
async def rate_game(
    game_id: int,
    data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    给游戏评分（0-10 分，支持两位小数）。
    重复提交会覆盖之前的评分，并自动重新计算游戏平均分。
    """
    return await set_rating(db, user_id=current_user.id, game_id=game_id, data=data)


@router.get(
    "/{game_id}/rating/me",
    response_model=RatingOut | None,
    summary="我的评分",
)
async def my_rating(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户对某游戏的评分，未评过分返回 null。"""
    return await get_user_rating(db, current_user.id, game_id)


@router.post(
    "/{game_id}/status",
    response_model=UserGameStatusOut,
    summary="设置游玩状态",
)
async def update_play_status(
    game_id: int,
    data: UserGameStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    设置游戏游玩状态：
    - 0=想玩  1=在玩  2=已完  3=搁置  4=弃坑
    """
    return await set_play_status(
        db, user_id=current_user.id, game_id=game_id, data=data
    )


@router.get(
    "/{game_id}/status/me",
    response_model=UserGameStatusOut | None,
    summary="我的游玩状态",
)
async def my_play_status(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户对某游戏的游玩状态，未设置返回 null。"""
    return await get_play_status(db, current_user.id, game_id)
