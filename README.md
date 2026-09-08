# star_gal

一个视觉小说 / Galgame 资料库与社区平台。以 VNDB、Bangumi(BGM) 数据为基础，提供游戏检索、标签浏览、评分与游玩状态、收藏评论、个人云存档等功能。

## 技术栈

**后端**
- FastAPI + Uvicorn
- SQLAlchemy + Alembic（MySQL / PyMySQL / aiomysql）
- Redis（会话与缓存）
- JWT（python-jose）+ passlib/argon2 密码哈希

**前端**（`stargal-frontend/`）
- Next.js 16 + React 19 + TypeScript
- Tailwind CSS 4

## 项目结构

```
star_gal/
├── app/                    # FastAPI 后端
│   ├── main.py             # 应用入口（路由注册、生命周期）
│   ├── api/                # 接口层：auth / game / tag / interaction / play / save / upload
│   ├── core/               # 配置、Redis 等基础设施
│   ├── crud/               # 数据库增删改查
│   ├── db/                 # 数据库连接与种子数据
│   ├── models/             # ORM 模型：game / character / tag / staff / producer / ranking / ...
│   ├── schemas/            # Pydantic 数据模型
│   └── services/           # 业务逻辑层
├── scripts/                # 数据导入脚本
│   ├── import_vndb.py      # 从本地 PostgreSQL vndb 库导入核心数据到 MySQL
│   └── import_bgm.py       # 用 Bangumi 归档数据补充中文简介、评分、别名
├── stargal-frontend/       # Next.js 前端
│   ├── app/                # 页面：login / register / dashboard / game / tags / saves
│   ├── components/         # UI 组件
│   ├── lib/                # API 客户端与工具
│   └── types/              # 类型定义
├── alembic.ini             # 数据库迁移配置
├── requirements.txt        # Python 依赖
└── .env                    # 环境变量（不入库）
```

## 功能模块（API 前缀 `/api/v1`）

| 模块 | 路由 | 说明 |
|------|------|------|
| 认证 | `/auth` | 注册、登录、登出（JWT） |
| 游戏 | `/games` | 游戏列表、搜索/筛选/分页、详情 |
| 标签 | `/tags` | 标签分类树、标签浏览 |
| 互动 | - | 评论、收藏、点赞 |
| 游玩 | `/games` | 评分、游玩状态（想玩/在玩/通关等） |
| 存档 | - | 个人云存档管理 |
| 上传 | `/uploads` | 分片文件上传 |

## 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.x
- Redis

## 快速开始

### 1. 配置环境变量

在项目根目录 `.env` 中配置（键名如下）：

```
MYSQL_USER / MYSQL_PASSWORD / MYSQL_HOST / MYSQL_PORT / MYSQL_DB
REDIS_HOST / REDIS_PORT / REDIS_PASSWORD / REDIS_DB
SECRET_KEY / ALGORITHM / ACCESS_TOKEN_EXPIRE_MINUTES
CORS_ORIGINS
```

### 2. 启动后端

```bash
pip install -r requirements.txt
alembic upgrade head          # 执行数据库迁移
uvicorn app.main:app --reload # 启动开发服务器，默认 http://127.0.0.1:8000
```

启动时会自动初始化种子数据并检查 Redis 连接；API 文档见 `http://127.0.0.1:8000/docs`。

### 3. 导入数据（可选）

```bash
python scripts/import_vndb.py   # 需要本地 PostgreSQL 的 vndb 数据库
python scripts/import_bgm.py    # 需要 Bangumi 归档 subject.jsonlines
```

### 4. 启动前端

```bash
cd stargal-frontend
npm install
npm run dev                     # http://localhost:3000
```

## License

私有项目，暂未开源。
