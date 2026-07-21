"""
角色模型
========

包含：角色(Character) / 角色别名(CharacterAlias) / 游戏-角色关联(GameCharacter)。
"""

import enum

from sqlalchemy import String, Text, Integer, Enum, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class CharSex(enum.IntEnum):
    """角色性别"""

    UNKNOWN = 0   # 未知/未设定
    MALE = 1      # 男
    FEMALE = 2    # 女
    BOTH = 3      # 双性(b)
    NONE = 4      # 无性别(n)


class CharRole(enum.IntEnum):
    """角色在某作品中的定位"""

    MAIN = 0      # 主角
    PRIMARY = 1   # 主要角色
    SIDE = 2      # 配角
    APPEARS = 3   # 客串/登场


class Character(Base, TimestampMixin, SoftDeleteMixin):
    """角色主表。"""

    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, comment="原名")
    name_cn: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True, comment="中文名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="角色介绍")
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="角色立绘/头像")

    sex: Mapped[CharSex] = mapped_column(Enum(CharSex), default=CharSex.UNKNOWN, comment="性别")
    blood_type: Mapped[str | None] = mapped_column(String(2), nullable=True, comment="血型 ")
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="身高(cm)")
    weight: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="体重(kg)")
    birthday: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="生日(mmdd, 0=未知)")
    #（原画）（三围）（来源）

    aliases: Mapped[list["CharacterAlias"]] = relationship(
        "CharacterAlias", back_populates="character", cascade="all, delete-orphan"
    )

    game_links: Mapped[list["GameCharacter"]] = relationship(
        "GameCharacter", back_populates="character", cascade="all, delete-orphan"
    )

    seiyuu_links: Mapped[list["GameSeiyuu"]] = relationship(
        "GameSeiyuu", back_populates="character", cascade="all, delete-orphan"
    )

    art_links: Mapped[list["GameCharacterArt"]] = relationship(
        "GameCharacterArt", back_populates="character", cascade="all, delete-orphan"
    )


class CharacterAlias(Base):
    """角色别名/多语言名表"""

    __tablename__ = "character_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, comment="别名/异名")
    latin: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="罗马音")

    character: Mapped["Character"] = relationship("Character", back_populates="aliases")


class GameCharacter(Base):
    """游戏-角色关联"""

    __tablename__ = "game_characters"
    __table_args__ = (
        UniqueConstraint("game_id", "character_id", name="uq_game_character"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    role: Mapped[CharRole] = mapped_column(Enum(CharRole), default=CharRole.APPEARS, index=True, comment="角色定位")

    character: Mapped["Character"] = relationship("Character", back_populates="game_links")
