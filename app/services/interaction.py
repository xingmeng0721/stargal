"""Service layer – comments, favorites, likes."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import interaction as interaction_crud
from app.schemas.interaction import (
    CommentCreate,
    CommentOut,
    CommentUserBrief,
    CommentListResponse,
    FavoriteOut,
    FavoriteListResponse,
    LikeCreate,
)
from app.schemas.game import GameCard


# ── Comments ─────────────────────────────────────────────────────────────


async def list_comments(
    db: AsyncSession,
    game_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> CommentListResponse:
    comments, total = await interaction_crud.get_comments_by_game(
        db, game_id, page=page, page_size=page_size
    )

    items = []
    for c in comments:
        user_info = getattr(c, "_user_info", None)
        user = (
            CommentUserBrief(id=c.user_id, username=user_info["username"], avatar_url=user_info["avatar_url"])
            if user_info
            else CommentUserBrief(id=c.user_id, username="unknown", avatar_url=None)
        )
        reply_items = []
        for r in getattr(c, "_replies", []):
            r_info = getattr(r, "_user_info", None)
            r_user = (
                CommentUserBrief(id=r.user_id, username=r_info["username"], avatar_url=r_info["avatar_url"])
                if r_info
                else CommentUserBrief(id=r.user_id, username="unknown", avatar_url=None)
            )
            reply_items.append(
                CommentOut(
                    id=r.id,
                    user=r_user,
                    game_id=r.game_id,
                    parent_id=r.parent_id,
                    content=r.content,
                    like_count=r.like_count,
                    reply_count=r.reply_count,
                    replies=[],
                    created_at=r.created_at,
                )
            )

        items.append(
            CommentOut(
                id=c.id,
                user=user,
                game_id=c.game_id,
                parent_id=None,
                content=c.content,
                like_count=c.like_count,
                reply_count=c.reply_count,
                replies=reply_items,
                created_at=c.created_at,
            )
        )

    return CommentListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


async def create_comment(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    data: CommentCreate,
    current_user: Optional[object] = None,
) -> CommentOut:
    comment = await interaction_crud.create_comment(
        db,
        user_id=user_id,
        game_id=game_id,
        content=data.content,
        parent_id=data.parent_id,
    )
    user_brief = None
    if current_user:
        # profile 关系未 eager load，async 下访问可能异常，安全兜底
        avatar = None
        try:
            prof = getattr(current_user, "profile", None)
            if prof is not None:
                avatar = getattr(prof, "avatar_url", None)
        except Exception:
            pass
        user_brief = CommentUserBrief(
            id=current_user.id,
            username=current_user.username,
            avatar_url=avatar,
        )
    return CommentOut(
        id=comment.id,
        user=user_brief,
        game_id=comment.game_id,
        parent_id=comment.parent_id,
        content=comment.content,
        like_count=comment.like_count,
        reply_count=comment.reply_count,
        replies=[],
        created_at=comment.created_at,
    )


# ── Favorites ────────────────────────────────────────────────────────────


async def list_favorites(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    folder: Optional[str] = None,
) -> FavoriteListResponse:
    favorites, total = await interaction_crud.get_user_favorites(
        db, user_id, page=page, page_size=page_size, folder=folder
    )

    items = []
    for f in favorites:
        game_obj = getattr(f, "_game", None)
        game_card = None
        if game_obj:
            game_card = GameCard(
                id=game_obj.id,
                title=game_obj.title,
                original_title=game_obj.original_title,
                cover_url=game_obj.cover_url,
                developer=game_obj.developer,
                release_date=game_obj.release_date,
                nsfw=game_obj.nsfw,
                bgm_score=game_obj.bgm_score,
                vndb_score=game_obj.vndb_score,
                rating_avg=game_obj.rating_avg,
                rating_count=game_obj.rating_count,
                view_count=game_obj.view_count,
                favorite_count=game_obj.favorite_count,
                download_count=game_obj.download_count,
                comment_count=game_obj.comment_count,
                tags=[],
            )
        items.append(
            FavoriteOut(
                id=f.id,
                game=game_card,
                folder=f.folder,
                created_at=f.created_at,
            )
        )

    return FavoriteListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


async def add_favorite(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    folder: Optional[str] = None,
) -> FavoriteOut:
    fav = await interaction_crud.add_favorite(
        db, user_id=user_id, game_id=game_id, folder=folder
    )
    return FavoriteOut(
        id=fav.id,
        game=None,
        folder=fav.folder,
        created_at=fav.created_at,
    )


async def remove_favorite(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
) -> bool:
    return await interaction_crud.remove_favorite(
        db, user_id=user_id, game_id=game_id
    )


# ── Likes ────────────────────────────────────────────────────────────────


async def toggle_like(
    db: AsyncSession,
    *,
    user_id: int,
    data: LikeCreate,
) -> bool:
    """Returns True if liked, False if unliked."""
    return await interaction_crud.toggle_like(
        db,
        user_id=user_id,
        target_type=data.target_type,
        target_id=data.target_id,
    )
