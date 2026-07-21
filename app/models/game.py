"""
游戏(条目)模型
==============

包含：游戏主表(Game) / 别名(GameAlias) / 截图(GameImage) / 统一资源(GameResource)。
"""

import enum
from datetime import date

from sqlalchemy import String, Text, Integer, BigInteger, Enum, ForeignKey, Date, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class GameStatus(enum.IntEnum):
    """
    游戏条目的发布/审核状态。
    """

    DRAFT = 0       # 草稿(上传中/未提交)
    PENDING = 1     # 待审核
    PUBLISHED = 2   # 已发布(对外可见)
    REJECTED = 3    # 审核未通过
    ARCHIVED = 4    # 已下架/归档


class ResourceType(enum.IntEnum):
    """游戏资源类型(统一可下载内容的分类)。"""

    GAME = 0     # 游戏本体
    PATCH = 1    # 补丁/升级档
    VOICE = 2    # 语音包
    GUIDE = 3    # 攻略/文档
    SAVE = 4     # 公开存档(由个人存档发布而来)
    OTHER = 9    # 其它


class Game(Base, TimestampMixin, SoftDeleteMixin):
    """游戏条目主表。"""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)

    # —— 基础元数据 ——
    title: Mapped[str] = mapped_column(String(200), index=True, comment="主标题")
    original_title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="原名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="主简介")
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True, comment="英文简介")
    description_ja: Mapped[str | None] = mapped_column(Text, nullable=True, comment="日文简介")
    description_zh: Mapped[str | None] = mapped_column(Text, nullable=True, comment="中文简介")
    cover_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="封面图地址")
    nsfw: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否含成人内容")

    developer: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True, comment="开发商/会社")
    publisher: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="发行商")
    release_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True, comment="发售日期")

    # —— 外部数据源标识/元数据
    bgm_id: Mapped[int | None] = mapped_column(
        Integer, unique=True, index=True, nullable=True, comment="对应 Bangumi 条目ID(匹配后回填)"
    )
    bgm_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True, comment="BGM 评分")
    bgm_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="BGM 类别内排名")

    # VNDB 数据 (新增)
    vndb_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, nullable=True, comment="对应 VNDB 条目ID(如 v2002)"
    )
    vndb_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True, comment="VNDB 评分")

    # —— 状态与归属 ——
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus), default=GameStatus.PENDING, index=True, comment="发布/审核状态"
    )
    uploader_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True, comment="上传者(用户)"
    )

    # —— 聚合/冗余统计(用于榜单、列表展示) ——
    rating_avg: Mapped[float] = mapped_column(Numeric(4, 2), default=0, comment="平均评分(冗余)")
    rating_count: Mapped[int] = mapped_column(Integer, default=0, comment="评分人数(冗余)")
    view_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="浏览量(冗余)")
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, comment="被收藏数(冗余)")
    download_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="下载次数(冗余)")
    comment_count: Mapped[int] = mapped_column(Integer, default=0, comment="评论数(冗余)")

    # —— 关系 ——
    aliases: Mapped[list["GameAlias"]] = relationship(
        "GameAlias", back_populates="game", cascade="all, delete-orphan"
    )
    images: Mapped[list["GameImage"]] = relationship(
        "GameImage", back_populates="game", cascade="all, delete-orphan"
    )
    resources: Mapped[list["GameResource"]] = relationship(
        "GameResource", back_populates="game", cascade="all, delete-orphan"
    )


class GameAlias(Base):
    """
    游戏别名表，支持多维/模糊搜索。
    """

    __tablename__ = "game_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(200), index=True, comment="别名/异名")
    lang: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="语言代码 zh/ja/en")

    game: Mapped["Game"] = relationship("Game", back_populates="aliases")


class GameImage(Base, TimestampMixin):
    """游戏截图/剧照表(封面单独放主表，这里是多张展示图)。"""

    __tablename__ = "game_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(255), comment="图片地址")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="展示排序，越小越靠前")

    game: Mapped["Game"] = relationship("Game", back_populates="images")


class GameResource(Base, TimestampMixin, SoftDeleteMixin):
    """游戏统一资源表(本体 / 补丁 / 语音 / 公开存档 等可下载内容)。
    """

    __tablename__ = "game_resources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True, comment="所属游戏")
    uploader_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True, comment="资源上传者"
    )

    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), default=ResourceType.GAME, index=True, comment="资源类型"
    )
    title: Mapped[str] = mapped_column(String(150), comment="资源标题(如 本体v1.2/汉化补丁/全线路存档)")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="资源说明")

    # —— 文件元数据(本体在对象存储) ——
    file_name: Mapped[str] = mapped_column(String(255), comment="原始文件名")
    storage_path: Mapped[str] = mapped_column(String(500), comment="存储路径/对象存储 key")
    file_size: Mapped[int] = mapped_column(BigInteger, comment="文件大小(字节)")
    file_hash: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True, comment="文件 SHA-256，用于秒传/校验/去重"
    )
    version: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="版本/分卷说明")

    # 公开存档资源 -> 来源个人存档
    source_save_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_saves.id", ondelete="SET NULL"), index=True, nullable=True,
        comment="若为公开存档资源,指向来源的个人存档ID"
    )

    download_count: Mapped[int] = mapped_column(BigInteger, default=0, comment="该资源下载次数")

    game: Mapped["Game"] = relationship("Game", back_populates="resources")
