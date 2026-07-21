"""Tag API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tag import TagCategoryOut, TagListResponse
from app.services.tag import get_tag_categories, list_tags

router = APIRouter(prefix="/tags", tags=["标签模块"])


@router.get("/categories", response_model=list[TagCategoryOut], summary="标签分类树")
async def tag_categories(db: AsyncSession = Depends(get_db)):
    """
    获取所有标签分类及其下属标签（树形结构），
    用于前端的标签筛选面板和标签云展示。
    """
    return await get_tag_categories(db)


@router.get("", response_model=TagListResponse, summary="标签列表")
async def tag_list(
    category_id: Optional[int] = Query(None, description="按分类 ID 筛选"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取标签扁平列表，可按分类过滤。
    按使用次数降序排列，方便前端展示热门标签。
    """
    return await list_tags(db, category_id=category_id)
