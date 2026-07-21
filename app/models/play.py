"""
游玩记录与评分模型
==================

包含：游玩状态/时长(UserGameStatus) / 游玩时段会话(PlaySession) / 评分(Rating)。

"""

import enum
from datetime import datetime

from sqlalchemy import Integer, BigInteger, Enum, ForeignKey, UniqueConstraint, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class PlayStatus(enum.IntEnum):
    """游玩状态机(参考 bgm 收藏状态)。"""

    WISH = 0       # 想玩
    PLAYING = 1    # 在玩
    FINISHED = 2   # 玩过/通关
    ON_HOLD = 3    # 搁置
    DROPPED = 4    # 抛弃


class UserGameStatus(Base, TimestampMixin):
    """用户对某游戏的状态汇总"""

    __tablename__ = "user_game_status"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="用户")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="游戏")

    status: Mapped[PlayStatus] = mapped_column(
        Enum(PlayStatus), default=PlayStatus.WISH, index=True, comment="当前游玩状态"
    )
    # 累计游玩时长(分钟)，由 PlaySession 汇总；用于「时长统计」和榜单
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, comment="累计游玩时长(分钟)")
    last_played_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="最后游玩时间")


class PlaySession(Base):
    """
    单次游玩会话(时长明细流水)。
    """

    __tablename__ = "play_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="用户")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="游戏")

    started_at: Mapped[datetime] = mapped_column(DateTime, comment="本次开始时间")
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="本次结束时间")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, comment="本次时长(分钟)")


class Rating(Base, TimestampMixin):
    """评分表。
    """

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game_rating"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="评分用户")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="被评分游戏")
    score: Mapped[float] = mapped_column(Numeric(4, 2), comment="评分(如 0.00~10.00)")
