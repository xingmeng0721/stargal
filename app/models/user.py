"""
用户与权限模型
"""

import enum
from datetime import datetime

from sqlalchemy import String, ForeignKey, Integer, Enum, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class UserStatus(enum.IntEnum):
    """用户账号状态，用整数枚举存储，兼顾可读性与存储效率。"""

    ACTIVE = 1       # 正常
    INACTIVE = 0     # 未激活
    BANNED = 2       # 封禁中


class Role(Base):
    """
    角色表
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, comment="角色名: admin, user, reviewer ...")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="角色说明")

    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    """用户账号表（鉴权核心）。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="登录用户名，唯一")
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True, comment="邮箱，可用于找回/通知")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="加盐哈希后的密码")

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, index=True, comment="账号状态"
    )

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), default=2, comment="角色外键")

    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="最后登录时间")

    # —— 冗余统计字段 ——
    game_count: Mapped[int] = mapped_column(Integer, default=0, comment="上传/拥有游戏数(冗余)")
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, comment="收藏数(冗余)")

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(Base, TimestampMixin):
    """用户展示资料表"""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称(可与用户名不同)")
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像地址")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True, comment="个性签名/简介")
    gender: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="性别: 0未知 1男 2女")

    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserBan(Base, TimestampMixin):
    """
    封禁记录表（管理模块用）。
    """

    __tablename__ = "user_bans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="被封禁用户")
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="执行封禁的管理员")
    reason: Mapped[str] = mapped_column(String(255), comment="封禁原因")
    expire_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="封禁到期时间，NULL=永久")
    is_active: Mapped[bool] = mapped_column(default=True, index=True, comment="该封禁是否仍生效")
