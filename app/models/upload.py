"""
分块上传与审核模型
==================

包含：上传任务(UploadTask) / 分块记录(UploadChunk)。

设计目标：支持「大文件分块上传 + 断点续传 + 秒传 + 审核」。
适用于「游戏上传」与「存档上传」两种场景(用 target_type 区分)。

分块上传流程(为什么要这两张表)：
1) 前端把大文件切成 N 块，先调用「初始化」接口创建一条 UploadTask，
   带上文件总大小、总块数、整体文件 hash、目标类型(游戏资源/存档)。
   - 若该 file_hash 已存在且审核通过 → 直接「秒传」，不必再传。
2) 前端逐块上传，每成功一块写一条/更新一条 UploadChunk(记录块序号、块hash)。
   - 断点续传：续传前查 UploadTask 已有哪些 chunk_index，跳过已传的块。
3) 全部块到齐后调用「合并」接口，服务端按序号合并、校验整体 hash，
   生成正式的 GameResource / GameSave，并把 UploadTask 标记为 COMPLETED。
4) 审核策略(结合本次需求)：
   - 游戏资源(GAME_RESOURCE)：需要审核，合并后进入审核流程(见 admin.py)。
   - 个人存档(GAME_SAVE)：私有存档【免审核】，合并后直接可用。

可维护性要点：
- 把「上传过程」和「最终产物」彻底分离：过程数据(任务/分块)可定期清理，
  最终产物(GameFile/GameSave)长期保留。互不污染。
- target_type 让同一套分块上传机制复用于多种业务，避免重复造轮子。
"""

import enum
from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class UploadTargetType(enum.IntEnum):
    """上传目标类型，决定合并后生成什么产物。"""

    GAME_RESOURCE = 0   # 游戏资源(本体/补丁/语音等，需审核)
    GAME_SAVE = 1       # 个人存档(私有免审核)


class UploadStatus(enum.IntEnum):
    """上传任务状态机。"""

    INIT = 0        # 已初始化，等待上传分块
    UPLOADING = 1   # 分块上传中
    MERGING = 2     # 分块齐全，合并中
    COMPLETED = 3   # 合并完成，已生成正式文件
    FAILED = 4      # 失败(校验不通过/超时等)


class UploadTask(Base, TimestampMixin):
    """分块上传任务(一次大文件上传 = 一条任务)。"""

    __tablename__ = "upload_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # upload_id：给前端用的唯一标识(通常是 UUID)，比自增ID更适合对外暴露
    upload_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="对外上传任务标识(UUID)")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="上传者")

    target_type: Mapped[UploadTargetType] = mapped_column(Enum(UploadTargetType), comment="上传目标类型")
    # 关联的游戏(本体或存档都需要知道属于哪个游戏)；游戏上传时可能先无ID，故可空
    game_id: Mapped[int | None] = mapped_column(
        ForeignKey("games.id"), index=True, nullable=True, comment="关联游戏(可后绑定)"
    )

    file_name: Mapped[str] = mapped_column(String(255), comment="原始文件名")
    file_size: Mapped[int] = mapped_column(BigInteger, comment="文件总大小(字节)")
    file_hash: Mapped[str] = mapped_column(String(64), index=True, comment="整体文件 SHA-256(用于秒传/合并校验)")

    total_chunks: Mapped[int] = mapped_column(Integer, comment="总分块数")
    uploaded_chunks: Mapped[int] = mapped_column(Integer, default=0, comment="已上传分块数(冗余,用于进度)")

    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus), default=UploadStatus.INIT, index=True, comment="上传任务状态"
    )
    expire_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="任务过期时间，过期未完成可被清理"
    )

    chunks: Mapped[list["UploadChunk"]] = relationship(
        "UploadChunk", back_populates="task", cascade="all, delete-orphan"
    )


class UploadChunk(Base):
    """单个分块记录。

    唯一约束 (task_id, chunk_index) 保证同一任务同一序号的块只记一次，
    重复上传同一块时做幂等更新，是断点续传的基础。
    """

    __tablename__ = "upload_chunks"
    __table_args__ = (
        UniqueConstraint("task_id", "chunk_index", name="uq_task_chunk_index"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("upload_tasks.id", ondelete="CASCADE"), index=True, comment="所属上传任务")

    chunk_index: Mapped[int] = mapped_column(Integer, comment="分块序号(从0或1开始,合并时按此排序)")
    chunk_size: Mapped[int] = mapped_column(Integer, comment="该块大小(字节)")
    chunk_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="该块hash,用于单块校验")
    storage_path: Mapped[str] = mapped_column(String(500), comment="该块临时存储路径")

    task: Mapped["UploadTask"] = relationship("UploadTask", back_populates="chunks")
