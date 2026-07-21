from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, reusable_oauth2
from app.core.redis import add_token_blacklist
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User, UserProfile, UserStatus
from app.schemas.user import UserCreate, UserOut, Token, UserLogin

router = APIRouter(prefix="/auth", tags=["认证模块"])


@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已被注册")

    new_user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role_id=2,  # 普通用户
    )

    new_user.profile = UserProfile()

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    # 查找用户
    result = await db.execute(select(User).where(User.username == user_in.username))
    user = result.scalar_one_or_none()

    # 验证密码
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 校验账号状态
    if user.status == UserStatus.BANNED:
        raise HTTPException(status_code=403, detail="该账号已被封禁")
    # if user.status == UserStatus.INACTIVE:
    #     raise HTTPException(status_code=403, detail="该账号尚未激活")

    # 记录最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # 生成 JWT
    access_token = create_access_token(subject=user.id)

    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/logout")
async def logout(
    token: str = Depends(reusable_oauth2),
    current_user: User = Depends(get_current_user),
):
    """退出登录：将当前的 Token 加入 Redis 黑名单。"""
    # 获取设置的过期时间（分钟），转换为秒，作为 Redis 的过期时间
    expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    await add_token_blacklist(token, expire_seconds)

    return {"message": "安全退出成功"}
