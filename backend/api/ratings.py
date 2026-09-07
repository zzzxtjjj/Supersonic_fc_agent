import sqlite3
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status

from backend.rating_auth import (
    get_current_rating_user_optional,
    require_current_rating_user,
)
from backend.ratings.api_service import (
    RatingTargetNotFound,
    get_rating_match_page,
    list_player_comments,
    post_comment,
    post_comment_like,
    post_rating_like,
    put_rating,
)
from backend.ratings.database import get_connection
from backend.schemas.comment import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    LikeToggleResponse,
)
from backend.schemas.rating import (
    RatingMatchPageResponse,
    RatingSubmitRequest,
    RatingSubmitResponse,
)


router = APIRouter(tags=["ratings"])


def get_rating_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _translate_error(exc: ValueError) -> HTTPException:
    if isinstance(exc, RatingTargetNotFound) or "不存在" in str(exc):
        code = status.HTTP_404_NOT_FOUND
    elif "权限" in str(exc):
        code = status.HTTP_403_FORBIDDEN
    else:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=code, detail=str(exc))


@router.get(
    "/ratings/matches/{match_id}",
    response_model=RatingMatchPageResponse,
)
async def get_match_rating_page(
    match_id: str,
    viewer_user_id: str | None = Depends(get_current_rating_user_optional),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> RatingMatchPageResponse:
    try:
        result = get_rating_match_page(
            connection,
            match_id=match_id,
            viewer_user_id=viewer_user_id,
        )
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return RatingMatchPageResponse(**result)


@router.put(
    "/ratings/matches/{match_id}/players/{player_id}",
    response_model=RatingSubmitResponse,
)
async def rate_player(
    match_id: str,
    player_id: str,
    payload: RatingSubmitRequest,
    user_id: str = Depends(require_current_rating_user),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> RatingSubmitResponse:
    try:
        result = put_rating(
            connection,
            match_id=match_id,
            player_id=player_id,
            user_id=user_id,
            score=payload.score,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return RatingSubmitResponse(**result)


@router.post(
    "/ratings/{rating_id}/like",
    response_model=LikeToggleResponse,
)
async def like_rating(
    rating_id: str,
    user_id: str = Depends(require_current_rating_user),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> LikeToggleResponse:
    try:
        result = post_rating_like(connection, rating_id=rating_id, user_id=user_id)
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return LikeToggleResponse(**result)


@router.get(
    "/ratings/matches/{match_id}/players/{player_id}/comments",
    response_model=CommentListResponse,
)
async def get_comments(
    match_id: str,
    player_id: str,
    viewer_user_id: str | None = Depends(get_current_rating_user_optional),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> CommentListResponse:
    try:
        comments = list_player_comments(
            connection,
            match_id=match_id,
            player_id=player_id,
            viewer_user_id=viewer_user_id,
        )
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return CommentListResponse(comments=comments)


@router.post(
    "/ratings/matches/{match_id}/players/{player_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_player_comment(
    match_id: str,
    player_id: str,
    payload: CommentCreateRequest,
    user_id: str = Depends(require_current_rating_user),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> CommentResponse:
    try:
        result = post_comment(
            connection,
            match_id=match_id,
            player_id=player_id,
            user_id=user_id,
            content=payload.content,
        )
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return CommentResponse(**result)


@router.post(
    "/comments/{comment_id}/like",
    response_model=LikeToggleResponse,
)
async def like_comment(
    comment_id: str,
    user_id: str = Depends(require_current_rating_user),
    connection: sqlite3.Connection = Depends(get_rating_connection),
) -> LikeToggleResponse:
    try:
        result = post_comment_like(connection, comment_id=comment_id, user_id=user_id)
    except ValueError as exc:
        raise _translate_error(exc) from exc
    return LikeToggleResponse(**result)
