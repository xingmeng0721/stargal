"""CRUD operations for Game model."""

from datetime import date
from typing import Optional

from sqlalchemy import case, func, select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game, GameAlias, GameImage, GameResource, GameStatus
from app.models.tag import GameTag, Tag


def _nulls_last_desc(column):
    """MySQL 不支持 NULLS LAST，用 CASE 把 NULL 排末尾。"""
    return [case((column.is_(None), 1), else_=0), column.desc()]


async def get_game_list(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    tag_names: Optional[list[str]] = None,
    developer: Optional[str] = None,
    nsfw: Optional[bool] = None,
    year: Optional[int] = None,
    # 接受 GameStatus 枚举 或 int（自动转换），防止外部传 int 导致 SQL 比较失败。
    # MySQL Enum 列存储的是成员名字符串（如 'PUBLISHED'），直接比较整数永远匹配不到。
    status: "GameStatus | int" = GameStatus.PUBLISHED,
    sort: str = "latest",
) -> tuple[list[Game], int]:
    """Return (games, total_count) with applied filters and pagination."""

    # 统一转换为枚举对象，保证 SQLAlchemy 生成正确的字符串比较
    if isinstance(status, int):
        try:
            status = GameStatus(status)
        except ValueError:
            status = GameStatus.PUBLISHED  # 非法值回退到已发布

    base = select(Game).where(Game.is_deleted == False, Game.status == status)
    count_base = select(func.count(Game.id)).where(
        Game.is_deleted == False, Game.status == status
    )

    # 关键词搜索：title / original_title / aliases
    if q:
        like = f"%{q}%"
        keyword_filter = or_(
            Game.title.ilike(like),
            Game.original_title.ilike(like),
        )
        alias_game_ids = (
            select(GameAlias.game_id).where(GameAlias.alias.ilike(like)).distinct()
        )
        keyword_filter = or_(keyword_filter, Game.id.in_(alias_game_ids))
        base = base.where(keyword_filter)
        count_base = count_base.where(keyword_filter)

    # 标签过滤（AND 语义：必须同时拥有所有指定标签）
    if tag_names:
        tag_game_ids = (
            select(GameTag.game_id)
            .join(Tag, GameTag.tag_id == Tag.id)
            .where(Tag.name.in_(tag_names))
            .group_by(GameTag.game_id)
            .having(func.count(GameTag.tag_id) >= len(tag_names))
        )
        base = base.where(Game.id.in_(tag_game_ids))
        count_base = count_base.where(Game.id.in_(tag_game_ids))

    # 开发商
    if developer:
        base = base.where(Game.developer.ilike(f"%{developer}%"))
        count_base = count_base.where(Game.developer.ilike(f"%{developer}%"))

    # NSFW
    if nsfw is not None:
        base = base.where(Game.nsfw == nsfw)
        count_base = count_base.where(Game.nsfw == nsfw)

    # 年份
    if year:
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        base = base.where(Game.release_date >= start, Game.release_date <= end)
        count_base = count_base.where(
            Game.release_date >= start, Game.release_date <= end
        )

    total = (await db.execute(count_base)).scalar() or 0

    # 排序（MySQL 兼容）
    if sort == "latest":
        order_clauses = _nulls_last_desc(Game.release_date)
    elif sort == "rating":
        order_clauses = _nulls_last_desc(Game.bgm_score)
    elif sort == "views":
        order_clauses = [Game.view_count.desc()]
    elif sort == "downloads":
        order_clauses = [Game.download_count.desc()]
    else:
        order_clauses = [Game.created_at.desc()]

    query = base.order_by(*order_clauses).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    games = list(result.scalars().all())

    return games, total


async def get_tags_for_games(
    db: AsyncSession, game_ids: list[int]
) -> dict[int, list[Tag]]:
    """批量加载多个游戏的标签。返回 {game_id: [Tag, ...]}。"""
    if not game_ids:
        return {}

    query = (
        select(GameTag.game_id, Tag)
        .join(Tag, GameTag.tag_id == Tag.id)
        .where(GameTag.game_id.in_(game_ids))
        .order_by(GameTag.weight.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    mapping: dict[int, list[Tag]] = {gid: [] for gid in game_ids}
    for game_id, tag in rows:
        mapping[game_id].append(tag)
    return mapping


async def get_game_detail(db: AsyncSession, game_id: int) -> Optional[Game]:
    """获取单个游戏及其别名 / 截图 / 资源（eager load）。

    ★ Bug Fix 2: selectinload 不支持链式 .order_by()；
      截图排序交由 Service 层在 Python 侧完成。
    """
    query = (
        select(Game)
        .where(Game.id == game_id, Game.is_deleted == False)
        .options(
            selectinload(Game.aliases),
            selectinload(Game.images),   # 排序在 service 层用 sorted() 处理
            selectinload(Game.resources),
        )
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_tags_for_game(db: AsyncSession, game_id: int) -> list[Tag]:
    """加载单个游戏的标签，按权重降序。"""
    query = (
        select(Tag)
        .join(GameTag, GameTag.tag_id == Tag.id)
        .where(GameTag.game_id == game_id)
        .order_by(GameTag.weight.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def increment_view_count(db: AsyncSession, game_id: int) -> None:
    """原子地将 view_count +1（不单独 commit，由调用方控制事务）。"""
    stmt = update(Game).where(Game.id == game_id).values(view_count=Game.view_count + 1)
    await db.execute(stmt)

