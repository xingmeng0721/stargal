"""
模型汇总
========

统一导入所有 model，作用有两个：
1) 让 `Base.metadata.create_all` 能识别到全部表(只有被导入的模型才会建表)。
   在 main.py 里只要 `from app.models import *` 或导入本包即可。
2) 方便其它模块统一从 app.models 引用，如 `from app.models import Game, User`。

新增模型时，记得在这里补充导入与 __all__，保持单一汇总入口(可维护性)。
"""

from app.models.base import TimestampMixin, SoftDeleteMixin
from app.models.user import (
    Role,
    User,
    UserProfile,
    UserBan,
    UserStatus,
)
from app.models.game import (
    Game,
    GameAlias,
    GameImage,
    GameResource,
    GameStatus,
    ResourceType,
)
from app.models.tag import (
    TagCategory,
    Tag,
    GameTag,
    TagType,
)
from app.models.interaction import (
    Comment,
    Like,
    Favorite,
    TargetType,
)
from app.models.play import (
    UserGameStatus,
    PlaySession,
    Rating,
    PlayStatus,
)
from app.models.save import (
    GameSave,
    SaveDownload,
    SaveVisibility,
)
from app.models.upload import (
    UploadTask,
    UploadChunk,
    UploadTargetType,
    UploadStatus,
)
from app.models.ranking import (
    RankingSnapshot,
    PeriodType,
    RankType,
)
from app.models.admin import (
    ReviewRecord,
    Report,
    AdminLog,
    ReviewTargetType,
    ReviewResult,
    ReportStatus,
)
from app.models.character import (
    Character,
    CharacterAlias,
    GameCharacter,
    CharSex,
    CharRole,
)
from app.models.producer import (
    Producer,
    GameProducer,
    ProducerType,
)
from app.models.staff import (
    Staff,
    GameStaff,
    GameSeiyuu,
    GameCharacterArt,
    CreditType,
)
from app.models.release import (
    Release,
    ReleasePlatform,
    GameRelease,
)

__all__ = [
    # base
    "TimestampMixin", "SoftDeleteMixin",
    # user
    "Role", "User", "UserProfile", "UserBan", "UserStatus",
    # game
    "Game", "GameAlias", "GameImage", "GameResource", "GameStatus", "ResourceType",
    # tag
    "TagCategory", "Tag", "GameTag", "TagType",
    # interaction
    "Comment", "Like", "Favorite", "TargetType",
    # play
    "UserGameStatus", "PlaySession", "Rating", "PlayStatus",
    # save
    "GameSave", "SaveDownload", "SaveVisibility",
    # upload
    "UploadTask", "UploadChunk", "UploadTargetType", "UploadStatus",
    # ranking
    "RankingSnapshot", "PeriodType", "RankType",
    # admin
    "ReviewRecord", "Report", "AdminLog",
    "ReviewTargetType", "ReviewResult", "ReportStatus",
    # character
    "Character", "CharacterAlias", "GameCharacter", "CharSex", "CharRole",
    # producer
    "Producer", "GameProducer", "ProducerType",
    # staff
    "Staff", "GameStaff", "GameSeiyuu", "GameCharacterArt", "CreditType",
    # release
    "Release", "ReleasePlatform", "GameRelease",
]
