from pydantic import BaseModel, ConfigDict, Field


# 注册请求
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


# 登录请求
class UserLogin(BaseModel):
    username: str
    password: str


# 响应数据：隐藏密码，只给前端看安全字段
class UserOut(BaseModel):
    id: int
    username: str
    role_id: int

    # 允许从 SQLAlchemy 对象直接转换
    model_config = ConfigDict(from_attributes=True)


# 用户资料
class UserProfileOut(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    gender: int | None = None

    model_config = ConfigDict(from_attributes=True)


# Token 响应
class Token(BaseModel):
    access_token: str
    token_type: str
