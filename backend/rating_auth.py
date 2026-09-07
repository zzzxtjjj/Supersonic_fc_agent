from fastapi import Depends, HTTPException, status

from backend.player_auth import get_current_player_user_optional


def get_current_rating_user_optional(
    user_id: str | None = Depends(get_current_player_user_optional),
) -> str | None:
    """Return the user established by the independent Player Session."""

    return user_id


def require_current_rating_user(
    user_id: str | None = Depends(get_current_rating_user_optional),
) -> str:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player authentication required.",
        )
    return user_id
