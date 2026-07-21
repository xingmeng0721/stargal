"""CRUD operations for chunked upload tasks."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.upload import UploadTask, UploadChunk, UploadTargetType, UploadStatus


async def check_instant_upload(
    db: AsyncSession, file_hash: str
) -> Optional[UploadTask]:
    """检查是否存在相同 hash 的已完成上传(秒传)。"""
    result = await db.execute(
        select(UploadTask).where(
            UploadTask.file_hash == file_hash,
            UploadTask.status == UploadStatus.COMPLETED,
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def init_upload_task(
    db: AsyncSession,
    *,
    user_id: int,
    target_type: int,
    game_id: Optional[int],
    file_name: str,
    file_size: int,
    file_hash: str,
    total_chunks: int,
) -> UploadTask:
    """初始化一个分块上传任务。"""
    tt = UploadTargetType(target_type)
    task = UploadTask(
        upload_id=str(uuid.uuid4()),
        user_id=user_id,
        target_type=tt,
        game_id=game_id,
        file_name=file_name,
        file_size=file_size,
        file_hash=file_hash,
        total_chunks=total_chunks,
        uploaded_chunks=0,
        status=UploadStatus.INIT,
        expire_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(task)
    await db.flush()
    await db.commit()
    await db.refresh(task)
    return task


async def get_upload_task(
    db: AsyncSession, upload_id: str, user_id: int
) -> Optional[UploadTask]:
    """获取上传任务(仅本人)。"""
    result = await db.execute(
        select(UploadTask).where(
            UploadTask.upload_id == upload_id,
            UploadTask.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_uploaded_chunk_indices(
    db: AsyncSession, task_id: int
) -> set[int]:
    """获取已上传的分块序号集合(断点续传用)。"""
    result = await db.execute(
        select(UploadChunk.chunk_index).where(UploadChunk.task_id == task_id)
    )
    return {row[0] for row in result.all()}


async def save_chunk(
    db: AsyncSession,
    *,
    task_id: int,
    chunk_index: int,
    chunk_size: int,
    chunk_hash: Optional[str],
    storage_path: str,
) -> UploadChunk:
    """保存分块记录(幂等：同一 chunk_index 不重复插入)。"""
    # 先检查是否已存在
    existing = await db.execute(
        select(UploadChunk).where(
            UploadChunk.task_id == task_id,
            UploadChunk.chunk_index == chunk_index,
        )
    )
    chunk = existing.scalar_one_or_none()
    if chunk:
        return chunk  # 幂等，已存在

    chunk = UploadChunk(
        task_id=task_id,
        chunk_index=chunk_index,
        chunk_size=chunk_size,
        chunk_hash=chunk_hash,
        storage_path=storage_path,
    )
    db.add(chunk)

    # 更新任务已上传分块数
    task_result = await db.execute(
        select(UploadTask).where(UploadTask.id == task_id)
    )
    task = task_result.scalar_one()
    task.uploaded_chunks = (task.uploaded_chunks or 0) + 1
    task.status = UploadStatus.UPLOADING

    await db.flush()
    await db.commit()
    await db.refresh(chunk)
    return chunk


async def mark_task_merging(
    db: AsyncSession, task_id: int
) -> Optional[UploadTask]:
    """标记任务为合并中。"""
    result = await db.execute(
        select(UploadTask).where(UploadTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        return None
    task.status = UploadStatus.MERGING
    await db.flush()
    await db.commit()
    await db.refresh(task)
    return task


async def mark_task_completed(
    db: AsyncSession, task_id: int
) -> Optional[UploadTask]:
    """标记任务为完成。"""
    result = await db.execute(
        select(UploadTask).where(UploadTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        return None
    task.status = UploadStatus.COMPLETED
    await db.flush()
    await db.commit()
    await db.refresh(task)
    return task


async def get_user_uploads(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[UploadTask], int]:
    """获取用户的上传任务列表。"""
    from sqlalchemy import func

    count_q = select(func.count(UploadTask.id)).where(
        UploadTask.user_id == user_id
    )
    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(
        select(UploadTask)
        .where(UploadTask.user_id == user_id)
        .order_by(UploadTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tasks = list(result.scalars().all())
    return tasks, total
