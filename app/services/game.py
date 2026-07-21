"""Service layer – game browsing, searching, detail."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import game as game_crud
from app.schemas.game import (
    GameCard,
    GameDetail,
    GameListResponse,
    TagBrief,
    GameAliasBrief,
    GameImageBrief,
    GameResourceBrief,
)


def _game_to_card(game, tags: list | None = None) -> GameCard:
    tag_briefs = [TagBrief(id=t.id, name=t.name) for t in (tags or [])]
    return GameCard(
        id=game.id,
        title=game.title,
        original_title=game.original_title,
        cover_url=game.cover_url,
        developer=game.developer,
        release_date=game.release_date,
        nsfw=game.nsfw,
        bgm_score=game.bgm_score,
        vndb_score=game.vndb_score,
        rating_avg=game.rating_avg,
        rating_count=game.rating_count,
        view_count=game.view_count,
        favorite_count=game.favorite_count,
        download_count=game.download_count,
        comment_count=game.comment_count,
        tags=tag_briefs,
    )


async def list_games(
    db: AsyncSession,
    *,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    developer: Optional[str] = None,
    nsfw: Optional[bool] = None,
    year: Optional[int] = None,
    sort: str = "latest",
    page: int = 1,
    page_size: int = 20,
) -> GameListResponse:
    tag_names = [t.strip() for t in tag.split(",")] if tag else None

    games, total = await game_crud.get_game_list(
        db,
        page=page,
        page_size=page_size,
        q=q,
        tag_names=tag_names,
        developer=developer,
        nsfw=nsfw,
        year=year,
        sort=sort,
    )

    game_ids = [g.id for g in games]
    tags_map = await game_crud.get_tags_for_games(db, game_ids)
    cards = [_game_to_card(g, tags_map.get(g.id, [])) for g in games]

    return GameListResponse(items=cards, total=total, page=page, page_size=page_size)


async def get_game_detail(
    db: AsyncSession, game_id: int, *, user_id: int | None = None
) -> Optional[GameDetail]:
    # ── 第一步：加载全部数据 ──────────────────────────────────────────────
    game = await game_crud.get_game_detail(db, game_id)  # 含 selectinload 关联
    if not game:
        return None

    tags = await game_crud.get_tags_for_game(db, game_id)

    is_fav = False
    if user_id:
        from app.crud.interaction import is_favorited
        is_fav = await is_favorited(db, user_id, game_id)

    # ── 第二步：在任何 commit 前，把所有 ORM 属性快照为纯 Python 值 ────────
    # 根本原因：await db.commit() 之后，即使 expire_on_commit=False，
    # SQLAlchemy 的异步 session 在访问关联对象的 backref 时仍会尝试懒加载，
    # 而此时已不在 greenlet 上下文中，导致 MissingGreenlet。
    # 解法：commit 前把所有值提取成普通 Python 对象，此后不再访问 ORM 实例。
    snap = {
        "id":               game.id,
        "title":            game.title,
        "original_title":   game.original_title,
        "description":      game.description,
        "description_zh":   game.description_zh,
        "description_en":   game.description_en,
        "description_ja":   game.description_ja,
        "cover_url":        game.cover_url,
        "nsfw":             game.nsfw,
        "developer":        game.developer,
        "publisher":        game.publisher,
        "release_date":     game.release_date,
        "bgm_id":           game.bgm_id,
        "bgm_score":        game.bgm_score,
        "bgm_rank":         game.bgm_rank,
        "vndb_id":          game.vndb_id,
        "vndb_score":       game.vndb_score,
        "rating_avg":       game.rating_avg,
        "rating_count":     game.rating_count,
        "view_count":       game.view_count,
        "favorite_count":   game.favorite_count,
        "download_count":   game.download_count,
        "comment_count":    game.comment_count,
        "status":           game.status.value if hasattr(game.status, "value") else int(game.status),
        "created_at":       game.created_at,
        "updated_at":       game.updated_at,
    }

    # 关联集合同样在 commit 前提取为纯 schema 对象
    alias_list = [
        GameAliasBrief(id=a.id, alias=a.alias, lang=a.lang)
        for a in game.aliases
    ]
    image_list = [
        GameImageBrief(id=i.id, url=i.url, sort_order=i.sort_order)
        for i in sorted(game.images, key=lambda x: x.sort_order)
    ]
    resource_list = [
        GameResourceBrief(
            id=r.id,
            resource_type=r.resource_type.value if hasattr(r.resource_type, "value") else int(r.resource_type),
            title=r.title,
            file_name=r.file_name,
            file_size=r.file_size,
            download_count=r.download_count,
            version=r.version,
            created_at=r.created_at,
        )
        for r in game.resources
        if not r.is_deleted
    ]
    tag_list = [TagBrief(id=t.id, name=t.name) for t in tags]

    # ── 第三步：所有只读数据已安全提取，现在才做写操作 + commit ────────────
    await game_crud.increment_view_count(db, game_id)
    await db.commit()

    # ── 第四步：用纯 Python 值构建响应，完全不再碰 ORM 实例 ────────────────
    return GameDetail(
        **snap,
        aliases=alias_list,
        images=image_list,
        tags=tag_list,
        resources=resource_list,
        is_favorited=is_fav,
    )
