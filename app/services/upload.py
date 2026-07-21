"""Service layer – chunked uploads."""

from typing import Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import upload as upload_crud
from app.schemas.upload import (
    UploadInitCreate,
    UploadTaskOut,
    ChunkUploadResponse,
    InstantUploadResponse,
)


def _task_to_out(task) -> UploadTaskOut:
    """将 ORM 对象转为输出 schema。"""
    return UploadTaskOut(
        id=task.id,
        upload_id=task.upload_id,
        user_id=task.user_id,
        target_type=int(task.target_type),
        game_id=task.game_id,
        file_name=task.file_name,
        file_size=task.file_size,
        file_hash=task.file_hash,
        total_chunks=task.total_chunks,
        uploaded_chunks=task.uploaded_chunks or 0,
        status=int(task.status),
        created_at=task.created_at,
    )


async def check_instant(
    db: AsyncSession, file_hash: str
) -> InstantUploadResponse:
    """秒传检查：hash 已存在则直接返回成功。"""
    existing = await upload_crud.check_instant_upload(db, file_hash)
    if existing:
        return InstantUploadResponse(
            exists=True,
            message="文件已存在，秒传成功",
            resource_id=existing.id,
        )
    return InstantUploadResponse(exists=False, message="文件不存在，需要上传")


async def init_upload(
    db: AsyncSession,
    user_id: int,
    data: UploadInitCreate,
) -> UploadTaskOut:
    """初始化分块上传任务。"""
    task = await upload_crud.init_upload_task(
        db,
        user_id=user_id,
        target_type=data.target_type,
        game_id=data.game_id,
        file_name=data.file_name,
        file_size=data.file_size,
        file_hash=data.file_hash,
        total_chunks=data.total_chunks,
    )
    return _task_to_out(task)


async def upload_chunk(
    db: AsyncSession,
    upload_id: str,
    user_id: int,
    chunk_index: int,
    chunk_hash: Optional[str],
    file: UploadFile,
) -> ChunkUploadResponse:
    """上传单个分块。"""
    task = await upload_crud.get_upload_task(db, upload_id, user_id)
    if not task:
        raise ValueError("上传任务不存在或无权限")

    # 校验分块序号
    if chunk_index < 0 or chunk_index >= task.total_chunks:
        raise ValueError(f"分块序号 {chunk_index} 超出范围 [0, {task.total_chunks})")

    # 读取文件内容并保存(实际项目应存入对象存储，这里记录路径)
    content = await file.read()
    chunk_size = len(content)
    # 临时存储路径(生产环境替换为对象存储)
    storage_path = f"uploads/chunks/{upload_id}/{chunk_index}"

    await upload_crud.save_chunk(
        db,
        task_id=task.id,
        chunk_index=chunk_index,
        chunk_size=chunk_size,
        chunk_hash=chunk_hash,
        storage_path=storage_path,
    )

    return ChunkUploadResponse(
        chunk_index=chunk_index,
        chunk_hash=chunk_hash,
        message="分块上传成功",
    )


async def get_upload_status(
    db: AsyncSession,
    upload_id: str,
    user_id: int,
) -> Optional[UploadTaskOut]:
    """查询上传任务状态(含已上传分块序号列表)。"""
    task = await upload_crud.get_upload_task(db, upload_id, user_id)
    if not task:
        return None
    return _task_to_out(task)


async def get_uploaded_chunks(
    db: AsyncSession,
    upload_id: str,
    user_id: int,
) -> set[int]:
    """获取已上传的分块序号集合(断点续传)。"""
    task = await upload_crud.get_upload_task(db, upload_id, user_id)
    if not task:
        return set()
    return await upload_crud.get_uploaded_chunk_indices(db, task.id)


async def merge_upload(
    db: AsyncSession,
    upload_id: str,
    user_id: int,
) -> Optional[UploadTaskOut]:
    """合并分块(标记任务完成)。

    实际生产环境中需要：
    1. 校验所有分块是否齐全
    2. 按序号合并文件
    3. 校验整体 hash
    4. 生成正式 GameResource / GameSave
    这里简化为直接标记完成。
    """
    task = await upload_crud.get_upload_task(db, upload_id, user_id)
    if not task:
        return None

    # 检查是否所有分块已上传
    uploaded = await upload_crud.get_uploaded_chunk_indices(db, task.id)
    if len(uploaded) < task.total_chunks:
        raise ValueError(
            f"分块不完整: 已上传 {len(uploaded)}/{task.total_chunks}"
        )

    # 标记合并中 → 完成
    await upload_crud.mark_task_merging(db, task.id)
    completed = await upload_crud.mark_task_completed(db, task.id)
    if not completed:
        return None
    return _task_to_out(completed)
