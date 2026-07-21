"""
种子数据(seed)
==============

使用：
  - 启动时：main.py 的 lifespan 会调用 seed_roles()。
  - 手动：在项目根执行  python -m app.db.seed
"""

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import Role

# 角色定义集中在此，新增角色只改这里
DEFAULT_ROLES = [
    {"id": 1, "name": "admin", "description": "管理员"},
    {"id": 2, "name": "user", "description": "普通用户"},
    {"id": 3, "name": "reviewer", "description": "审核员"},
]


async def seed_roles() -> None:
    """初始化/补齐默认角色(幂等)。"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Role.id))
        existing_ids = {row[0] for row in result.all()}

        to_add = [
            Role(**r) for r in DEFAULT_ROLES if r["id"] not in existing_ids
        ]
        if to_add:
            session.add_all(to_add)
            await session.commit()
            print(f"已初始化角色: {[r.name for r in to_add]}")
        else:
            print("角色已存在，无需初始化")


async def seed_all() -> None:
    """统一入口：以后有更多种子数据(默认标签分类等)都在这里编排。"""
    await seed_roles()


if __name__ == "__main__":
    asyncio.run(seed_all())
