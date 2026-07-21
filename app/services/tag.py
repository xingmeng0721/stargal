"""Service layer – tags."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import tag as tag_crud
from app.schemas.tag import TagOut, TagCategoryOut, TagListResponse


async def get_tag_categories(db: AsyncSession) -> list[TagCategoryOut]:
    """返回所有分类及其标签（Python 侧排序，避免 selectinload.order_by 问题）。"""
    categories = await tag_crud.get_tag_categories(db)
    result = []
    for cat in categories:
        # ★ Fix: 排序由 Python 完成（crud 层已去掉 selectinload.order_by）
        sorted_tags = sorted(cat.tags, key=lambda t: t.usage_count, reverse=True)
        tags = [
            TagOut(
                id=t.id,
                name=t.name,
                description=t.description,
                usage_count=t.usage_count,
                category_name=cat.name,
                category_type=cat.type.value if hasattr(cat.type, "value") else cat.type,
            )
            for t in sorted_tags
        ]
        result.append(
            TagCategoryOut(
                id=cat.id,
                name=cat.name,
                type=cat.type.value if hasattr(cat.type, "value") else cat.type,
                sort_order=cat.sort_order,
                tags=tags,
            )
        )
    return result


async def list_tags(
    db: AsyncSession, *, category_id: Optional[int] = None
) -> TagListResponse:
    tags = await tag_crud.get_all_tags(db, category_id=category_id)
    items = []
    for t in tags:
        # ★ Fix: category 已在 crud 层 selectinload 预加载，安全访问
        cat_name = t.category.name if t.category else None
        cat_type = (
            t.category.type.value
            if t.category and hasattr(t.category.type, "value")
            else (t.category.type if t.category else None)
        )
        items.append(
            TagOut(
                id=t.id,
                name=t.name,
                description=t.description,
                usage_count=t.usage_count,
                category_name=cat_name,
                category_type=cat_type,
            )
        )
    return TagListResponse(items=items, total=len(items))

