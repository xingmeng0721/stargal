"""Service layer – game saves."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import save as save_crud
from app.schemas.save import SaveCreate, SaveOut, SaveListResponse


def _save_to_out(save) -> SaveOut:
    """将 ORM 对象转为输出 schema。"""
    return SaveOut(
        id=save.id,
        game_id=save.game_id,
        user_id=save.user_id,
        title=save.title,
        description=save.description,
        storage_path=save.storage_path,
        file_size=save.file_size,
        file_hash=save.file_hash,
        visibility=int(save.visibility),
        published_at=save.published_at,
        download_count=save.download_count,
        created_at=save.created_at,
        updated_at=save.updated_at,
    )


async def list_user_saves(
    db: AsyncSession,
    user_id: int,
    *,
    game_id: Optional[int] = None,
    visibility: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> SaveListResponse:
    """获取用户存档列表。"""
    saves, total = await save_crud.get_user_saves(
        db, user_id, game_id=game_id, visibility=visibility,
        page=page, page_size=page_size,
    )
    return SaveListResponse(
        items=[_save_to_out(s) for s in saves],
        total=total,
        page=page,
        page_size=page_size,
    )


async def list_public_saves(
    db: AsyncSession,
    game_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> SaveListResponse:
    """获取某游戏的公开存档列表。"""
    saves, total = await save_crud.get_public_saves_for_game(
        db, game_id, page=page, page_size=page_size,
    )
    return SaveListResponse(
        items=[_save_to_out(s) for s in saves],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_save(
    db: AsyncSession,
    user_id: int,
    data: SaveCreate,
) -> SaveOut:
    """创建存档。"""
    save = await save_crud.create_save(
        db,
        user_id=user_id,
        game_id=data.game_id,
        title=data.title,
        description=data.description,
        storage_path=data.storage_path,
        file_size=data.file_size,
        file_hash=data.file_hash,
        visibility=data.visibility,
    )
    return _save_to_out(save)


async def delete_save(
    db: AsyncSession,
    save_id: int,
    user_id: int,
) -> bool:
    """软删除存档(仅本人可操作)。"""
    return await save_crud.soft_delete_save(db, save_id, user_id)


async def publish_save(
    db: AsyncSession,
    save_id: int,
    user_id: int,
) -> Optional[SaveOut]:
    """将私有存档发布为公开。"""
    save = await save_crud.publish_save(db, save_id, user_id)
    if save is None:
        return None
    return _save_to_out(save)
