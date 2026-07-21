"""CRUD operations for play-related models – ratings and play status."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.play import Rating, UserGameStatus, PlayStatus


# ── Ratings ──────────────────────────────────────────────────────────────


async def get_user_rating(
    db: AsyncSession, user_id: int, game_id: int
) -> Optional[Rating]:
    result = await db.execute(
        select(Rating).where(
            Rating.user_id == user_id, Rating.game_id == game_id
        )
    )
    return result.scalar_one_or_none()


async def set_rating(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    score: Decimal,
) -> Rating:
    """Create or update a user's rating for a game.

    整个操作在单个事务中完成：先写入评分，再重算聚合，保证数据一致性。
    """
    existing = await get_user_rating(db, user_id, game_id)

    if existing:
        existing.score = score
        rating = existing
    else:
        rating = Rating(user_id=user_id, game_id=game_id, score=score)
        db.add(rating)

    # flush 让 SQLAlchemy 把 SQL 发到数据库（但不 commit）
    await db.flush()

    # 在同一个事务内重算游戏平均分
    agg = await db.execute(
        select(
            func.avg(Rating.score).label("avg"),
            func.count(Rating.id).label("cnt"),
        ).where(Rating.game_id == game_id)
    )
    row = agg.one()
    avg_score = Decimal(str(row.avg or 0)).quantize(Decimal("0.01"))
    count = row.cnt or 0

    stmt = (
        update(Game)
        .where(Game.id == game_id)
        .values(rating_avg=avg_score, rating_count=count)
    )
    await db.execute(stmt)

    # 一次性 commit，保证评分和聚合更新的原子性
    await db.commit()
    await db.refresh(rating)
    return rating


# ── Play status ──────────────────────────────────────────────────────────


async def get_user_game_status(
    db: AsyncSession, user_id: int, game_id: int
) -> Optional[UserGameStatus]:
    result = await db.execute(
        select(UserGameStatus).where(
            UserGameStatus.user_id == user_id,
            UserGameStatus.game_id == game_id,
        )
    )
    return result.scalar_one_or_none()


async def set_user_game_status(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    status: int,
) -> UserGameStatus:
    """设置游玩状态。将前端传入的 int 转换为 PlayStatus 枚举，兼容 MySQL ENUM。"""
    # 将原始 int 转为 MySQL ENUM 所需的枚举成员
    ps = PlayStatus(status)

    existing = await get_user_game_status(db, user_id, game_id)

    if existing:
        existing.status = ps
        await db.flush()
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        ugs = UserGameStatus(user_id=user_id, game_id=game_id, status=ps)
        db.add(ugs)
        await db.flush()
        await db.commit()
        await db.refresh(ugs)
        return ugs
