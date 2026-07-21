"""Upload API endpoints – chunked file upload."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.upload import (
    UploadInitCreate,
    UploadTaskOut,
    ChunkUploadResponse,
    InstantUploadResponse,
)
from app.services.upload import (
    check_instant,
    init_upload,
    upload_chunk,
    get_upload_status,
    get_uploaded_chunks,
    merge_upload,
)

router = APIRouter(prefix="/uploads", tags=["上传模块"])


@router.get(
    "/instant-check",
    response_model=InstantUploadResponse,
    summary="秒传检查",
)
async def instant_check(
    file_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查文件 hash 是否已存在，存在则秒传成功。"""
    return await check_instant(db, file_hash)


@router.post(
    "/init",
    response_model=UploadTaskOut,
    status_code=201,
    summary="初始化分块上传",
)
async def init_upload_endpoint(
    data: UploadInitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建分块上传任务，返回 upload_id 和任务信息。"""
    return await init_upload(db, current_user.id, data)


@router.post(
    "/{upload_id}/chunks/{chunk_index}",
    response_model=ChunkUploadResponse,
    summary="上传分块",
)
async def upload_chunk_endpoint(
    upload_id: str,
    chunk_index: int,
    file: UploadFile = File(...),
    chunk_hash: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传单个分块(支持 multipart/form-data)。"""
    try:
        return await upload_chunk(
            db, upload_id, current_user.id,
            chunk_index, chunk_hash, file,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{upload_id}",
    response_model=UploadTaskOut,
    summary="查询上传状态",
)
async def upload_status(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询上传任务状态和进度。"""
    result = await get_upload_status(db, upload_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="上传任务不存在或无权限")
    return result


@router.get(
    "/{upload_id}/chunks",
    summary="已上传分块列表(断点续传)",
)
async def uploaded_chunks(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取已上传的分块序号集合，用于断点续传时跳过已传块。"""
    indices = await get_uploaded_chunks(db, upload_id, current_user.id)
    return {"uploaded_chunks": sorted(indices)}


@router.post(
    "/{upload_id}/merge",
    response_model=UploadTaskOut,
    summary="合并分块",
)
async def merge_upload_endpoint(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """所有分块上传完毕后调用，合并为完整文件。"""
    try:
        result = await merge_upload(db, upload_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="上传任务不存在或无权限")
    return result
