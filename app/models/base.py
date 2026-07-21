"""
公共基础组件
===========

这里定义所有 model 复用的「混入类(Mixin)」与通用枚举。

"""

from datetime import datetime
from sqlalchemy import func, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    时间戳混入：创建时间 + 更新时间。
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="最后更新时间",
    )


class SoftDeleteMixin:
    """
    软删除混入：用标记位代替物理删除。
    查询业务数据时统一加 `where is_deleted = False` 即可隐藏已删除内容，
    同时保留数据用于审计、恢复与统计。
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="是否已软删除"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="软删除时间，未删除为 NULL"
    )
