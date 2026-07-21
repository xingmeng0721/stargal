"""
排行榜模型
==========

包含：榜单快照(RankingSnapshot)。


可维护性要点：
- 用 (period_type, period_key, rank_type) 描述「哪种周期 + 哪一期 + 按什么排」，
  扩展新榜单维度只需加枚举值，不改表结构。
- period_key 用字符串(如 '2026-06-28' / '2026-W26' / '2026-06')表达具体哪一期，
  通用且易读、易按期查询。
"""

import enum

from sqlalchemy import Integer, BigInteger, Enum, ForeignKey, String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class PeriodType(enum.IntEnum):
    """榜单周期类型。"""

    DAILY = 0     # 日榜
    WEEKLY = 1    # 周榜
    MONTHLY = 2   # 月榜


class RankType(enum.IntEnum):
    """排名维度(按什么排)。"""

    VIEW = 0        # 浏览量
    DOWNLOAD = 1    # 下载量
    RATING = 2      # 评分
    FAVORITE = 3    # 收藏量
    HOT = 4         # 综合热度(加权)


class RankingSnapshot(Base, TimestampMixin):
    """榜单快照：某周期、某维度下，某游戏的排名与得分。"""

    __tablename__ = "ranking_snapshots"
    __table_args__ = (
        UniqueConstraint("period_type", "period_key", "rank_type", "game_id", name="uq_ranking_entry"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    period_type: Mapped[PeriodType] = mapped_column(Enum(PeriodType), index=True, comment="周期类型(日/周/月)")
    period_key: Mapped[str] = mapped_column(String(20), index=True, comment="具体期次,如 2026-06-28 / 2026-W26 / 2026-06")
    rank_type: Mapped[RankType] = mapped_column(Enum(RankType), index=True, comment="排名维度")

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="游戏")
    rank: Mapped[int] = mapped_column(Integer, comment="名次(1=第一)")
    score: Mapped[float] = mapped_column(Numeric(12, 2), default=0, comment="该维度得分(浏览数/下载数/加权热度等)")
