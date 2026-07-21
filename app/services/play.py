"""Service layer – ratings and play status."""

from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import play as play_crud
from app.schemas.play import (
    RatingCreate,
    RatingOut,
    UserGameStatusCreate,
    UserGameStatusOut,
)


async def set_rating(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    data: RatingCreate,
) -> RatingOut:
    rating = await play_crud.set_rating(
        db, user_id=user_id, game_id=game_id, score=data.score
    )
    return RatingOut(
        id=rating.id,
        user_id=rating.user_id,
        game_id=rating.game_id,
        score=rating.score,
        created_at=rating.created_at,
    )


async def get_user_rating(
    db: AsyncSession, user_id: int, game_id: int
) -> Optional[RatingOut]:
    rating = await play_crud.get_user_rating(db, user_id, game_id)
    if not rating:
        return None
    return RatingOut(
        id=rating.id,
        user_id=rating.user_id,
        game_id=rating.game_id,
        score=rating.score,
        created_at=rating.created_at,
    )


async def set_play_status(
    db: AsyncSession,
    *,
    user_id: int,
    game_id: int,
    data: UserGameStatusCreate,
) -> UserGameStatusOut:
    ugs = await play_crud.set_user_game_status(
        db, user_id=user_id, game_id=game_id, status=data.status
    )
    return UserGameStatusOut(
        id=ugs.id,
        user_id=ugs.user_id,
        game_id=ugs.game_id,
        status=ugs.status if isinstance(ugs.status, int) else ugs.status.value,
        total_minutes=ugs.total_minutes,
        last_played_at=ugs.last_played_at,
        created_at=ugs.created_at,
    )


async def get_play_status(
    db: AsyncSession, user_id: int, game_id: int
) -> Optional[UserGameStatusOut]:
    ugs = await play_crud.get_user_game_status(db, user_id, game_id)
    if not ugs:
        return None
    return UserGameStatusOut(
        id=ugs.id,
        user_id=ugs.user_id,
        game_id=ugs.game_id,
        status=ugs.status if isinstance(ugs.status, int) else ugs.status.value,
        total_minutes=ugs.total_minutes,
        last_played_at=ugs.last_played_at,
        created_at=ugs.created_at,
    )
