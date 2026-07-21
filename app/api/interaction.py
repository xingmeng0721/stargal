"""Interaction API endpoints – comments, favorites, likes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.interaction import (
    CommentCreate,
    CommentOut,
    CommentListResponse,
    FavoriteCreate,
    FavoriteOut,
    FavoriteListResponse,
    LikeCreate,
)
from app.services.interaction import (
    list_comments,
    create_comment,
    list_favorites,
    add_favorite,
    remove_favorite,
    toggle_like,
)

router = APIRouter(tags=["互动模块"])


# ── Comments ─────────────────────────────────────────────────────────────


@router.get(
    "/games/{game_id}/comments",
    response_model=CommentListResponse,
    summary="游戏评论列表",
)
async def game_comments(
    game_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    获取某游戏的评论列表（楼中楼结构）。
    顶层评论按时间倒序，每条评论包含嵌套的回复列表。
    """
    return await list_comments(db, game_id, page=page, page_size=page_size)


@router.post(
    "/games/{game_id}/comments",
    response_model=CommentOut,
    status_code=201,
    summary="发表评论",
)
async def post_comment(
    game_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发表评论或回复（需要登录）。设置 parent_id 为回复。"""
    return await create_comment(
        db, user_id=current_user.id, game_id=game_id, data=data,
        current_user=current_user,
    )


# ── Favorites ────────────────────────────────────────────────────────────


@router.get(
    "/users/me/favorites",
    response_model=FavoriteListResponse,
    summary="我的收藏列表",
)
async def my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    folder: Optional[str] = Query(None, description="收藏夹名称"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的收藏列表，可按收藏夹分组筛选。"""
    return await list_favorites(
        db, current_user.id, page=page, page_size=page_size, folder=folder
    )


@router.post(
    "/favorites",
    response_model=FavoriteOut,
    status_code=201,
    summary="收藏游戏",
)
async def fav_game(
    data: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """收藏一个游戏，可指定收藏夹分组。"""
    try:
        return await add_favorite(
            db,
            user_id=current_user.id,
            game_id=data.game_id,
            folder=data.folder,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="该游戏已在收藏中")


@router.delete(
    "/favorites/{game_id}",
    summary="取消收藏",
)
async def unfav_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消收藏一个游戏。"""
    ok = await remove_favorite(db, user_id=current_user.id, game_id=game_id)
    if not ok:
        raise HTTPException(status_code=404, detail="未找到该收藏记录")
    return {"message": "已取消收藏"}


# ── Likes ────────────────────────────────────────────────────────────────


@router.post(
    "/likes/toggle",
    summary="点赞 / 取消点赞",
)
async def like_toggle(
    data: LikeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    切换点赞状态。
    - target_type: 0=游戏, 1=评论
    - 已点赞则取消，未点赞则添加
    """
    liked = await toggle_like(db, user_id=current_user.id, data=data)
    return {"liked": liked}
