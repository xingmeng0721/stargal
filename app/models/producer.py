"""
厂商模型
========

包含：厂商(Producer) / 游戏-厂商关联(GameProducer)。

"""

import enum

from sqlalchemy import String, Text, Integer, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ProducerType(enum.IntEnum):
    """厂商类型(对应 vndb producer_type)。"""

    COMPANY = 0      # 公司/会社(co)
    INDIVIDUAL = 1   # 个人(in)
    AMATEUR = 2      # 同人/业余团体(ng)


class Producer(Base, TimestampMixin, SoftDeleteMixin):
    """厂商主表(会社/品牌/个人)。"""

    __tablename__ = "producers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, comment="厂商名")
    latin_name: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True, comment="罗马音/拉丁化名")
    type: Mapped[ProducerType] = mapped_column(Enum(ProducerType), default=ProducerType.COMPANY, comment="类型")
    lang: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="主要语言/地区")
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True, comment="别名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="厂商介绍")

    game_links: Mapped[list["GameProducer"]] = relationship(
        "GameProducer", back_populates="producer", cascade="all, delete-orphan"
    )


class GameProducer(Base):
    """游戏-厂商关联(关联对象，区分开发/发行)。"""

    __tablename__ = "game_producers"
    __table_args__ = (
        UniqueConstraint("game_id", "producer_id", name="uq_game_producer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    producer_id: Mapped[int] = mapped_column(ForeignKey("producers.id", ondelete="CASCADE"), index=True)
    is_developer: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为开发商")
    is_publisher: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为发行商")

    producer: Mapped["Producer"] = relationship("Producer", back_populates="game_links")
