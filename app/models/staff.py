"""
制作人员模型
============

包含：制作人员(Staff) / 游戏-职务关联(GameStaff) / 游戏-声优关联(GameSeiyuu)。

设计参考：
- vndb 的 staff / staff_alias / vn_staff / vn_seiyuu：
  - staff 是人(可能有多个署名 alias)，关联用全局唯一的 alias id(aid)。
  - vn_staff：某人以某职务(脚本/原画/音乐/导演/翻译…)参与某作品。
  - vn_seiyuu：声优(staff)为某作品里的某角色(character)配音。

为什么把「职务」和「声优」分两张关联表？
- 职务关联只涉及 游戏<->人 + 职务类型。
- 声优关联额外涉及 角色(character)，是 游戏<->人<->角色 三方关系，
  字段不同，分表更清晰。

可维护性要点：
- 用 vndb 的 aid 作为 staff.id(全局唯一)，导入与关联都以 aid 为准，简单稳定。
"""

import enum

from sqlalchemy import String, Text, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models import Character
from app.models.base import TimestampMixin, SoftDeleteMixin


class CreditType(enum.IntEnum):
    """职务类型(对应 vndb credit_type)。"""

    SCENARIO = 0      # 脚本
    CHARDESIGN = 1    # 人物设计
    ART = 2           # 美术/原画
    MUSIC = 3         # 音乐
    SONGS = 4         # 歌曲
    DIRECTOR = 5      # 导演
    TRANSLATOR = 6    # 翻译
    EDITOR = 7        # 编辑
    QA = 8            # 质检
    STAFF = 9         # 其它staff


class Staff(Base, TimestampMixin, SoftDeleteMixin):
    """制作人员主表(以 vndb 的 alias id 即 aid 为主键)。"""

    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False, comment="人员ID(沿用vndb全局aid)")
    name: Mapped[str] = mapped_column(String(200), index=True, comment="署名(展示用)")
    latin_name: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True, comment="罗马音/拉丁化名")
    lang: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="主要语言")
    gender: Mapped[str | None] = mapped_column(String(2), nullable=True, comment="性别 m/f")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="人员介绍")


class GameStaff(Base):
    """游戏-职务关联(某人以某职务参与某作品)。
    """

    __tablename__ = "game_staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), index=True)
    role: Mapped[CreditType] = mapped_column(Enum(CreditType), index=True, comment="职务")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")


class GameSeiyuu(Base):
    """游戏-声优关联(某声优为某作品的某角色配音)。"""

    __tablename__ = "game_seiyuu"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), index=True, comment="声优")
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True, comment="配音角色")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注")

    character: Mapped["Character"] = relationship("Character", back_populates="seiyuu_links")


class GameCharacterArt(Base):
    """游戏-角色原画关联(某画师为某作品的某角色绘制原画/人设)。"""

    __tablename__ = "game_character_art"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), index=True, comment="原画师")
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True, comment="对应角色")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注(如: SD原画/辅助原画)")

    # 补全关联映射
    character: Mapped["Character"] = relationship("Character", back_populates="art_links")
