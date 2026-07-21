"""
存档模型：个人私有云存档 / 公开分享
====================================

包含：存档(GameSave) / 存档下载记录(SaveDownload)。

【本次优化重点：个人私有云存档(亮点功能)】
- 每个玩家都有「只属于自己、只对自己开放」的私有存档云空间。
- 私有存档(visibility=PRIVATE)：上传【不需要审核】，立即可用，仅本人可见/下载。
- 公开存档(visibility=PUBLIC)：玩家主动「发布」后，会同步在游戏界面以一条
  GameResource(resource_type=SAVE) 展示，供他人下载。
- 一张表用 visibility 区分两种用途：私有是默认与主场景，公开是可选的分享。

"""

import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, BigInteger, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class SaveVisibility(enum.IntEnum):
    """存档可见性。

    PRIVATE 是默认值：体现「个人私有云存档」这一主场景，免审核、仅自己可见。
    PUBLIC 表示玩家已把该存档分享到游戏界面(对应一条 GameResource)。
    """

    PRIVATE = 0   # 私有(仅自己，免审核)
    PUBLIC = 1    # 公开(已分享到游戏界面)


class GameSave(Base, TimestampMixin, SoftDeleteMixin):
    """玩家存档表(私有云存档为主，可选择公开分享)。"""

    __tablename__ = "game_saves"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="存档所属用户")
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="所属游戏")

    title: Mapped[str] = mapped_column(String(100), comment="存档标题(如 真结局前/全线路)")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="存档说明")

    # —— 文件元数据(本体在对象存储) ——
    storage_path: Mapped[str] = mapped_column(String(500), comment="存储路径/对象存储 key")
    file_size: Mapped[int] = mapped_column(BigInteger, comment="文件大小(字节)")
    file_hash: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True, comment="文件 SHA-256，用于校验/秒传/去重"
    )

    # —— 可见性(亮点核心) ——
    visibility: Mapped[SaveVisibility] = mapped_column(
        Enum(SaveVisibility), default=SaveVisibility.PRIVATE, index=True,
        comment="可见性: 私有(默认,免审核) / 公开(已分享)"
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="发布为公开的时间，私有为 NULL"
    )

    download_count: Mapped[int] = mapped_column(Integer, default=0, comment="被下载次数(公开后才有意义,冗余)")

    downloads: Mapped[list["SaveDownload"]] = relationship(
        "SaveDownload", back_populates="save", cascade="all, delete-orphan"
    )


class SaveDownload(Base):
    """存档下载记录(主要针对公开存档)。

    记录「谁在何时下载了哪个存档」，用于：下载量统计、防滥用/限流、
    用户的下载历史。私有存档一般只有本人下载，记录可选。
    """

    __tablename__ = "save_downloads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    save_id: Mapped[int] = mapped_column(ForeignKey("game_saves.id", ondelete="CASCADE"), index=True, comment="存档")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="下载用户")
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True, comment="下载来源IP(支持IPv6)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="下载时间")

    save: Mapped["GameSave"] = relationship("GameSave", back_populates="downloads")
