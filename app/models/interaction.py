"""
互动模型：评论 / 点赞 / 收藏
============================

包含：评论(Comment) / 点赞(Like) / 收藏(Favorite)。

"""

import enum

from sqlalchemy import String, Text, Integer, BigInteger, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class TargetType(enum.IntEnum):
    """点赞/举报等行为的目标类型(多态标识)。"""

    GAME = 0      # 游戏
    COMMENT = 1   # 评论


class Comment(Base, TimestampMixin, SoftDeleteMixin):
    """评论表，支持楼中楼回复。"""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="评论者")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="所属游戏")

    # 自关联：回复某条评论时指向父评论；顶层评论为 NULL
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id"), index=True, nullable=True, comment="父评论(楼中楼)"
    )

    content: Mapped[str] = mapped_column(Text, comment="评论内容")
    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数(冗余)")
    reply_count: Mapped[int] = mapped_column(Integer, default=0, comment="回复数(冗余)")

    replies: Mapped[list["Comment"]] = relationship(
        "Comment", backref="parent", remote_side=[id]
    )


class Like(Base, TimestampMixin):
    """点赞表(多态：可点赞游戏或评论)。
    """

    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_like_target"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="点赞用户")
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), comment="点赞对象类型")
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="点赞对象ID")


class Favorite(Base, TimestampMixin):
    """收藏表(用户收藏游戏)。
    """

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_favorite_game"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="收藏用户")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="被收藏游戏")
    folder: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="收藏夹分组名")
