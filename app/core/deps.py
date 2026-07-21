from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import is_token_blacklisted  # 导入黑名单校验
from app.db.session import get_db
from app.models.user import User, UserStatus

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ADMIN_ROLE_ID = 1


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    # 黑名单校验（已登出的 token 立即失效）
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该 Token 已失效，请重新登录",
        )

    # 解析 JWT
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效 Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 解析失败")

    # 查询用户
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 4. 状态校验：封禁用户即使持有有效 token 也拒绝访问
    if user.status == UserStatus.BANNED:
        raise HTTPException(status_code=403, detail="该账号已被封禁")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """管理员依赖：供管理模块的接口复用，非管理员一律 403。"""
    if current_user.role_id != ADMIN_ROLE_ID:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(optional_oauth2),
) -> User | None:
    """可选认证：未登录返回 None，已登录返回用户对象。适用于匿名可访问但登录后有更多功能的接口。"""
    if token is None:
        return None
    try:
        if await is_token_blacklisted(token):
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user and user.status != UserStatus.BANNED:
            return user
        return None
    except JWTError:
        return None
