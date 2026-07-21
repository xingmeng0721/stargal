from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.game import router as game_router
from app.api.tag import router as tag_router
from app.api.interaction import router as interaction_router
from app.api.play import router as play_router
from app.api.save import router as save_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.core.redis import redis_client
from app.db.seed import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。
    """
    # 1. 初始化种子数据(角色)
    try:
        await seed_all()
    except Exception as e:
        # 种子失败通常意味着还没执行迁移
        print(f"[WARN] 种子数据初始化失败(请确认已执行 `alembic upgrade head`): {e}")

    # 2. 检查 Redis 连接
    try:
        await redis_client.ping()
        print("[OK] Redis 连接成功")
    except Exception as e:
        print(f"[WARN] Redis 连接失败: {e}")

    yield

    # 3. 停止时清理资源
    await redis_client.close()


app = FastAPI(title="star_gal API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # 允许的来源列表
    allow_origins=settings.CORS_ORIGINS,
    # 允许跨域发送 Cookie
    allow_credentials=True,
    # 允许的请求方法 (GET, POST, PUT, DELETE 等)
    allow_methods=["*"],
    # 允许的请求头 (Authorization, Content-Type 等)
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(game_router, prefix="/api/v1")
app.include_router(tag_router, prefix="/api/v1")
app.include_router(interaction_router, prefix="/api/v1")
app.include_router(play_router, prefix="/api/v1")
app.include_router(save_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
