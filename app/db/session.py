from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # 开启日志
    pool_pre_ping=True # 自动检查连接是否存活
)

# 2. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 3. 创建模型基类
class Base(DeclarativeBase):
    pass

# 4. 依赖注入函数：每个请求进来时获取数据库连接，处理完自动关闭
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()