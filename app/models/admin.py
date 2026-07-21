"""
管理模块模型
============

包含：审核记录(ReviewRecord) / 举报(Report) / 管理操作日志(AdminLog)。

设计目标：支撑「游戏上传审核」「内容举报处理」「管理行为可追溯」。

"""

import enum
from datetime import datetime

from sqlalchemy import String, Text, BigInteger, Integer, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class ReviewTargetType(enum.IntEnum):
    """可被审核的对象类型。"""
    GAME = 0        # 游戏上传
    GAME_SAVE = 1   # 存档
    COMMENT = 2     # 评论


class ReviewResult(enum.IntEnum):
    """审核结果。"""

    PENDING = 0    # 待审核
    APPROVED = 1   # 通过
    REJECTED = 2   # 驳回


class ReviewRecord(Base, TimestampMixin):
    """审核记录(一次审核 = 一条)。"""

    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    target_type: Mapped[ReviewTargetType] = mapped_column(Enum(ReviewTargetType), index=True, comment="审核对象类型")
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="审核对象ID")

    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True, comment="审核员(待审核时为空)"
    )
    result: Mapped[ReviewResult] = mapped_column(
        Enum(ReviewResult), default=ReviewResult.PENDING, index=True, comment="审核结果"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核意见/驳回理由")
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="审核完成时间")


class ReportStatus(enum.IntEnum):
    """举报处理状态。"""

    PENDING = 0     # 待处理
    RESOLVED = 1    # 已处理(举报成立并处置)
    DISMISSED = 2   # 已驳回(举报不成立)


class Report(Base, TimestampMixin):
    """举报表(用户举报违规内容)。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="举报人")
    target_type: Mapped[ReviewTargetType] = mapped_column(Enum(ReviewTargetType), index=True, comment="被举报对象类型")
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="被举报对象ID")

    reason: Mapped[str] = mapped_column(String(255), comment="举报理由")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="补充说明")

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.PENDING, index=True, comment="处理状态"
    )
    handler_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="处理该举报的管理员"
    )
    handled_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="处理时间")


class AdminLog(Base, TimestampMixin):
    """管理操作日志(安全审计)。
    """

    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="操作管理员")
    action: Mapped[str] = mapped_column(String(50), index=True, comment="操作类型")

    target_type: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作对象类型(可选)")
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="操作对象ID(可选)")

    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="操作详情(JSON,灵活记录变更内容)")
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True, comment="操作来源IP")
