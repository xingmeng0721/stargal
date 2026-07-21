import redis.asyncio as redis
from redis.exceptions import RedisError
from fastapi import HTTPException

from app.core.config import settings

# 创建异步 Redis 连接池
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=3,
)


async def is_token_blacklisted(token: str) -> bool:
    """
    检查 token 是否在登出黑名单中。
    捕获 RedisError(涵盖连接/超时等所有 redis 异常)。
    """
    try:
        res = await redis_client.get(f"blacklist:{token}")
        return res is not None
    except RedisError:
        raise HTTPException(status_code=503, detail="身份验证系统异常（Redis）")


async def add_token_blacklist(token: str, expire_sec: int):
    """把 token 加入黑名单，过期时间与 token 剩余有效期一致。"""
    try:
        await redis_client.setex(f"blacklist:{token}", expire_sec, "logout")
    except RedisError:
        raise HTTPException(status_code=503, detail="退出登录失败，系统资源异常")
