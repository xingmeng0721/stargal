"""CRUD operations for game saves."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.save import GameSave, SaveVisibility


async def get_user_saves(
    db: AsyncSession,
    user_id: int,
    *,
    game_id: Optional[int] = None,
    visibility: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[GameSave], int]:
    """获取用户的存档列表。"""
    where_clauses = [
        GameSave.user_id == user_id,
        GameSave.is_deleted == False,
    ]
    if game_id is not None:
        where_clauses.append(GameSave.game_id == game_id)
    if visibility is not None:
        where_clauses.append(GameSave.visibility == SaveVisibility(visibility))

    count_q = select(func.count(GameSave.id)).where(*where_clauses)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(GameSave)
        .where(*where_clauses)
        .order_by(GameSave.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    saves = list(result.scalars().all())
    return saves, total


async def get_public_saves_for_game(
    db: AsyncSession,
    game_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[GameSave], int]:
    """获取某游戏的公开存档列表。"""
    where_clauses = [
        GameSave.game_id == game_id,
        GameSave.visibility == SaveVisibility.PUBLIC,
        GameSave.is_deleted == False,
    ]

    count_q = select(func.count(GameSave.id)).where(*where_clauses)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(GameSave)
        .where(*where_clauses)
        .order_by(GameSave.download_count.desc(), GameSave.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    saves = list(result.scalars().all())
    return saves, total


async def get_save_by_id(
    db: AsyncSession, save_id: int
) -> Optional[GameSave]:
    """根据 ID 获取存档(排除软删除)。"""
    result = await db.execute(
        select(GameSave).where(
            GameSave.id == save_id, GameSave.is_deleted == False
        )
    )
    return result.scalar_one_or_none()


async def create_save(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    title: str,
    description: Optional[str],
    storage_path: str,
    file_size: int,
    file_hash: Optional[str],
    visibility: int = 0,
) -> GameSave:
    """创建存档记录。"""
    vis = SaveVisibility(visibility)
    save = GameSave(
        user_id=user_id,
        game_id=game_id,
        title=title,
        description=description,
        storage_path=storage_path,
        file_size=file_size,
        file_hash=file_hash,
        visibility=vis,
        published_at=datetime.now(timezone.utc) if vis == SaveVisibility.PUBLIC else None,
    )
    db.add(save)
    await db.flush()
    await db.commit()
    await db.refresh(save)
    return save


async def soft_delete_save(
    db: AsyncSession, save_id: int, user_id: int
) -> bool:
    """软删除存档(仅本人可操作)。"""
    result = await db.execute(
        update(GameSave)
        .where(
            GameSave.id == save_id,
            GameSave.user_id == user_id,
            GameSave.is_deleted == False,
        )
        .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
    )
    if result.rowcount:  # type: ignore[union-attr]
        await db.commit()
        return True
    return False


async def publish_save(
    db: AsyncSession, save_id: int, user_id: int
) -> Optional[GameSave]:
    """将私有存档发布为公开。"""
    result = await db.execute(
        select(GameSave).where(
            GameSave.id == save_id,
            GameSave.user_id == user_id,
            GameSave.visibility == SaveVisibility.PRIVATE,
            GameSave.is_deleted == False,
        )
    )
    save = result.scalar_one_or_none()
    if not save:
        return None

    save.visibility = SaveVisibility.PUBLIC
    save.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    await db.refresh(save)
    return save
