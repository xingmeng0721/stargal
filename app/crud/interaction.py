"""CRUD operations for interactions – comments, favorites, likes."""

from typing import Optional

from sqlalchemy import func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Comment, Favorite, Like, TargetType
from app.models.game import Game
from app.models.user import User, UserProfile


# ── Comments ─────────────────────────────────────────────────────────────


async def get_comments_by_game(
    db: AsyncSession,
    game_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Comment], int]:
    """Return top-level comments (with nested replies) for a game.

    Note: Comment model doesn't define a `user` relationship,
    so we join User table in the query to attach user info.
    """
    # Count top-level only
    count_q = select(func.count(Comment.id)).where(
        Comment.game_id == game_id,
        Comment.parent_id.is_(None),
        Comment.is_deleted == False,
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch top-level comments
    query = (
        select(Comment)
        .where(
            Comment.game_id == game_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted == False,
        )
        .order_by(Comment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    comments = list(result.scalars().all())

    if not comments:
        return comments, total

    # ── Batch load users for top-level comments ──────────────────────────
    user_ids = [c.user_id for c in comments]
    user_query = (
        select(User.id, User.username, UserProfile.avatar_url)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .where(User.id.in_(user_ids))
    )
    user_result = await db.execute(user_query)
    user_map = {
        row.id: {"username": row.username, "avatar_url": row.avatar_url}
        for row in user_result
    }
    for c in comments:
        c._user_info = user_map.get(c.user_id)  # type: ignore[attr-defined]

    # ── Batch load ALL replies in a single query (fix N+1) ───────────────
    parent_ids = [c.id for c in comments]
    reply_query = (
        select(Comment)
        .where(
            Comment.parent_id.in_(parent_ids),
            Comment.is_deleted == False,
        )
        .order_by(Comment.created_at.asc())
    )
    reply_result = await db.execute(reply_query)
    all_replies = list(reply_result.scalars().all())

    # Group replies by parent_id
    replies_by_parent: dict[int, list[Comment]] = {}
    reply_user_ids: set[int] = set()
    for r in all_replies:
        replies_by_parent.setdefault(r.parent_id, []).append(r)
        reply_user_ids.add(r.user_id)

    # Batch load users for replies
    reply_user_map: dict[int, dict] = {}
    if reply_user_ids:
        reply_user_query = (
            select(User.id, User.username, UserProfile.avatar_url)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .where(User.id.in_(reply_user_ids))
        )
        reply_user_result = await db.execute(reply_user_query)
        reply_user_map = {
            row.id: {"username": row.username, "avatar_url": row.avatar_url}
            for row in reply_user_result
        }

    # Attach replies and user info to each top-level comment
    for c in comments:
        c_replies = replies_by_parent.get(c.id, [])
        for r in c_replies:
            r._user_info = reply_user_map.get(r.user_id)  # type: ignore[attr-defined]
        c._replies = c_replies  # type: ignore[attr-defined]

    return comments, total


async def create_comment(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    content: str,
    parent_id: Optional[int] = None,
) -> Comment:
    comment = Comment(
        user_id=user_id,
        game_id=game_id,
        content=content,
        parent_id=parent_id,
    )
    db.add(comment)

    # Update parent reply_count if replying
    if parent_id:
        stmt = (
            update(Comment)
            .where(Comment.id == parent_id)
            .values(reply_count=Comment.reply_count + 1)
        )
        await db.execute(stmt)

    # Update game comment_count
    stmt = (
        update(Game)
        .where(Game.id == game_id)
        .values(comment_count=Game.comment_count + 1)
    )
    await db.execute(stmt)

    await db.flush()
    await db.commit()
    await db.refresh(comment)
    return comment


# ── Favorites ────────────────────────────────────────────────────────────


async def get_user_favorites(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    folder: Optional[str] = None,
) -> tuple[list[Favorite], int]:
    base_where = [Favorite.user_id == user_id]
    if folder:
        base_where.append(Favorite.folder == folder)

    count_q = select(func.count(Favorite.id)).where(*base_where)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Favorite)
        .where(*base_where)
        .order_by(Favorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    favorites = list(result.scalars().all())

    # Batch load games for card display — exclude soft-deleted
    if favorites:
        game_ids = [f.game_id for f in favorites]
        game_query = select(Game).where(
            Game.id.in_(game_ids), Game.is_deleted == False
        )
        game_result = await db.execute(game_query)
        game_map = {g.id: g for g in game_result.scalars().all()}
        for f in favorites:
            f._game = game_map.get(f.game_id)  # type: ignore[attr-defined]

    return favorites, total


async def add_favorite(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    folder: Optional[str] = None,
) -> Favorite:
    fav = Favorite(user_id=user_id, game_id=game_id, folder=folder)
    db.add(fav)

    # Update game favorite_count
    stmt = (
        update(Game)
        .where(Game.id == game_id)
        .values(favorite_count=Game.favorite_count + 1)
    )
    await db.execute(stmt)

    await db.flush()
    await db.commit()
    await db.refresh(fav)
    return fav


async def remove_favorite(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
) -> bool:
    result = await db.execute(
        delete(Favorite).where(
            Favorite.user_id == user_id, Favorite.game_id == game_id
        )
    )
    if result.rowcount:  # type: ignore[union-attr]
        stmt = (
            update(Game)
            .where(Game.id == game_id)
            .values(favorite_count=func.greatest(Game.favorite_count - 1, 0))
        )
        await db.execute(stmt)
        await db.commit()
        return True
    return False


async def is_favorited(
    db: AsyncSession, user_id: int, game_id: int
) -> bool:
    result = await db.execute(
        select(Favorite.id).where(
            Favorite.user_id == user_id, Favorite.game_id == game_id
        )
    )
    return result.scalar_one_or_none() is not None


# ── Likes ────────────────────────────────────────────────────────────────


async def toggle_like(
    db: AsyncSession,
    *,
    user_id: int,
    target_type: int,
    target_id: int,
) -> bool:
    """Toggle a like. Returns True if liked, False if unliked.

    MySQL ENUM 列需要传入枚举成员而非原始 int，否则报 Data Truncated。
    """
    # 将前端传入的 int 转换为 MySQL ENUM 所需的枚举成员
    tt = TargetType(target_type)

    existing = await db.execute(
        select(Like).where(
            Like.user_id == user_id,
            Like.target_type == tt,
            Like.target_id == target_id,
        )
    )
    like = existing.scalar_one_or_none()

    if like:
        await db.delete(like)
        await db.commit()
        return False
    else:
        new_like = Like(
            user_id=user_id, target_type=tt, target_id=target_id
        )
        db.add(new_like)
        await db.flush()
        await db.commit()
        return True
