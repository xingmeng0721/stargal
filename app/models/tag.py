"""
标签模型
========

包含：标签分类(TagCategory) / 标签(Tag) / 游戏-标签关联(GameTag)。

设计参考：
- vndb 的标签系统是核心：标签有「分类」(剧情/萌点/技术等)，
  且游戏与标签的关联带「权重/投票数」(这个标签有多贴合这个游戏)，
  用于排序展示和更精准的搜索/推荐。
- bgm：标签也分类，且统计每个标签被使用的次数(热门标签)。

为什么用「关联表带额外字段」而不是简单多对多？
- 多对多通常用一张只有两个外键的中间表。但 Galgame 标签需要权重/投票，
  所以中间表升级为带业务字段的实体(GameTag)，这是关联对象模式(association object)。
- 这样做的好处：标签搜索可以按权重排序，推荐可以基于标签相似度计算。
"""

import enum

from sqlalchemy import String, Integer, Enum, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class TagType(enum.IntEnum):
    """标签大类，便于前端分组展示与搜索筛选。"""

    CONTENT = 0   # 剧情/内容(如 治愈、催泪)
    MOE = 1       # 萌点(如 傲娇、双马尾)
    TECH = 2      # 技术/制作(如 全语音、3D)
    OTHER = 3     # 其它


class TagCategory(Base):
    """标签分类表。

    把分类单独建表(而不是在 Tag 上写死字符串)，方便后台动态管理分类、
    调整分类名称或排序，而不用改代码。
    """

    __tablename__ = "tag_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, comment="分类名")
    type: Mapped[TagType] = mapped_column(Enum(TagType), default=TagType.OTHER, comment="分类大类")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="展示排序")

    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="category")


class Tag(Base, TimestampMixin):
    """标签表。"""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="标签名")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="标签说明")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("tag_categories.id"), index=True, nullable=True, comment="所属分类"
    )
    # 冗余统计
    usage_count: Mapped[int] = mapped_column(Integer, default=0, index=True, comment="被使用次数(冗余)")

    category: Mapped["TagCategory"] = relationship("TagCategory", back_populates="tags")
    game_links: Mapped[list["GameTag"]] = relationship("GameTag", back_populates="tag")


class GameTag(Base):
    """
    游戏-标签关联表(关联对象，带权重)。
    """

    __tablename__ = "game_tags"
    __table_args__ = (UniqueConstraint("game_id", "tag_id", name="uq_game_tag"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), index=True)

    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=0, comment="标签权重/相关度评分")
    vote_count: Mapped[int] = mapped_column(Integer, default=0, comment="投票该标签的人数")

    tag: Mapped["Tag"] = relationship("Tag", back_populates="game_links")
