"""Save API endpoints – personal cloud saves."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.save import SaveCreate, SaveOut, SaveListResponse
from app.services.save import (
    list_user_saves,
    list_public_saves,
    create_save,
    delete_save,
    publish_save,
)

router = APIRouter(tags=["存档模块"])


@router.get(
    "/users/me/saves",
    response_model=SaveListResponse,
    summary="我的存档列表",
)
async def my_saves(
    game_id: Optional[int] = Query(None, description="按游戏筛选"),
    visibility: Optional[int] = Query(None, description="0=私有 1=公开"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的存档列表，可按游戏/可见性筛选。"""
    return await list_user_saves(
        db, current_user.id,
        game_id=game_id, visibility=visibility,
        page=page, page_size=page_size,
    )


@router.get(
    "/games/{game_id}/saves",
    response_model=SaveListResponse,
    summary="游戏公开存档列表",
)
async def game_public_saves(
    game_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取某游戏的公开存档列表(匿名可访问)。"""
    return await list_public_saves(
        db, game_id, page=page, page_size=page_size,
    )


@router.post(
    "/saves",
    response_model=SaveOut,
    status_code=201,
    summary="创建存档",
)
async def create_save_endpoint(
    data: SaveCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建存档记录(文件本体需先通过上传模块上传)。"""
    return await create_save(db, current_user.id, data)


@router.delete(
    "/saves/{save_id}",
    summary="删除存档",
)
async def delete_save_endpoint(
    save_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除存档(仅本人可操作)。"""
    ok = await delete_save(db, save_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="存档不存在或无权限")
    return {"message": "存档已删除"}


@router.post(
    "/saves/{save_id}/publish",
    response_model=SaveOut,
    summary="发布存档为公开",
)
async def publish_save_endpoint(
    save_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将私有存档发布为公开(同步到游戏资源列表)。"""
    result = await publish_save(db, save_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="存档不存在、已公开或无权限")
    return result
