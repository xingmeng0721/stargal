"""CRUD operations for Tag model."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag, TagCategory, GameTag


async def get_tag_categories(db: AsyncSession) -> list[TagCategory]:
    """返回所有标签分类及其标签（树形）。

    ★ Bug Fix 3: selectinload 不支持链式 .order_by()。
      改用两步：先加载分类+标签，服务层再按 usage_count 排序，
      或在 relationship 上配置 order_by（这里选最稳妥的：
      用独立 selectinload，排序在 service 侧 Python 完成）。
    """
    query = (
        select(TagCategory)
        .options(selectinload(TagCategory.tags))
        .order_by(TagCategory.sort_order)
    )
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def get_all_tags(
    db: AsyncSession,
    *,
    category_id: Optional[int] = None,
    limit: int = 200,
) -> list[Tag]:
    """返回标签列表，可按分类过滤。

    ★ Bug Fix 4: 异步 session 下懒加载会抛 MissingGreenlet。
      必须用 selectinload 提前加载 Tag.category，
      否则 services/tag.py 里访问 t.category.name 会崩溃。
    """
    query = (
        select(Tag)
        .options(selectinload(Tag.category))
        .order_by(Tag.usage_count.desc())
    )
    if category_id is not None:
        query = query.where(Tag.category_id == category_id)
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    result = await db.execute(select(Tag).where(Tag.name == name))
    return result.scalar_one_or_none()
