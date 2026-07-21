"""
发行版本模型
============

包含：发行版本(Release) / 版本平台(ReleasePlatform) / 游戏-版本关联(GameRelease)。

设计参考：
- vndb 的 releases / releases_platforms / releases_vn：
  同一部作品(VN)会有多个「发行版本」(初版/全年龄版/移植版/汉化补丁…)，
  每个版本有自己的发售日、平台、年龄分级、是否免费/补丁/官方等属性。

为什么版本独立成表？
- 一个游戏多个版本是 galgame 的常态(PC版/移植版/各语言版)，
  版本信息(平台、发售日、分级)随版本不同，必须独立存储。
- 下载/资源也可以按版本组织。

可维护性要点：
- Release 与 Game 多对多(一个版本可能对应多部合集VN)，用关联表 GameRelease。
- 平台是一对多枚举，单独放 ReleasePlatform 表。
"""

import enum
from datetime import date

from sqlalchemy import String, Text, Integer, Enum, ForeignKey, Boolean, SmallInteger, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Release(Base, TimestampMixin, SoftDeleteMixin):
    """发行版本主表。"""

    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(250), nullable=True, comment="版本标题")
    released: Mapped[date | None] = mapped_column(Date, index=True, nullable=True, comment="发售日期")
    minage: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="年龄分级(0-18)")

    is_patch: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为补丁(如汉化补丁)")
    is_freeware: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否免费")
    is_official: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否官方发行")
    has_ero: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否含成人内容")

    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    platforms: Mapped[list["ReleasePlatform"]] = relationship(
        "ReleasePlatform", back_populates="release", cascade="all, delete-orphan"
    )


class ReleasePlatform(Base):
    """版本-平台(一个版本可发布在多个平台)。"""

    __tablename__ = "release_platforms"
    __table_args__ = (
        UniqueConstraint("release_id", "platform", name="uq_release_platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(10), index=True, comment="平台代码 win/ps4/swi 等")

    release: Mapped["Release"] = relationship("Release", back_populates="platforms")


class GameRelease(Base):
    """游戏-版本关联(一个版本可对应一/多部VN)。"""

    __tablename__ = "game_releases"
    __table_args__ = (
        UniqueConstraint("game_id", "release_id", name="uq_game_release"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True)
    # 版本与VN的关系类型(complete/partial/trial)，存短字符串
    rtype: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="complete/partial/trial")
