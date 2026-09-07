import math
import sqlite3

from backend.ratings.repository import (
    create_comment as create_comment_record,
    create_or_update_rating,
    get_comment,
    get_rating,
    get_user_player_id,
    is_rating_member,
    toggle_comment_like as toggle_comment_like_record,
    toggle_like,
)

from backend.api.season_data import load_players, list_seasons


def submit_rating(
    connection: sqlite3.Connection,
    *,
    rating_id: str,
    user_id: str,
    season_id: str,
    match_id: str,
    player_id: str,
    score: float,
    reason: str | None,
    created_at: str,
    updated_at: str,
) -> str:

    # 1. 检查这个用户是否有该赛季评分权限
    if not is_rating_member(
        connection,
        user_id,
        season_id,
    ):
        raise ValueError("你没有这个赛季的评分权限")

    # 2. 检查评分范围
    if not (0 <= score <= 10):
        raise ValueError("评分必须在 0 到 10 之间")

    # 3. 检查是否符合 0.1 分步长
    if not math.isclose(score * 10, round(score * 10), abs_tol=1e-9):
        raise ValueError("评分必须以 0.1 为步长")

    # 4. 清理和检查评分理由
    if reason is not None:
        reason = reason.strip()

        if reason == "":
            reason = None

        elif len(reason) > 100:
            raise ValueError("评分理由不能超过 100 个字符")

    # 5. 真正交给 Repository 写数据库
    actual_rating_id = create_or_update_rating(
        connection,
        rating_id=rating_id,
        user_id=user_id,
        season_id=season_id,
        match_id=match_id,
        player_id=player_id,
        score=score,
        reason=reason,
        created_at=created_at,
        updated_at=updated_at,
    )

    return actual_rating_id


def toggle_rating_like(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    rating_id: str,
    created_at: str,
) -> bool:
    if get_rating(connection, rating_id) is None:
        raise ValueError("评分不存在")
    if not is_supersonic_player(connection, user_id):
        raise ValueError("你没有社区互动权限")
    return toggle_like(
        connection,
        user_id=user_id,
        rating_id=rating_id,
        created_at=created_at,
    )


def is_supersonic_player(
    connection: sqlite3.Connection,
    user_id: str,
) -> bool:

    player_id = get_user_player_id(
        connection,
        user_id,
    )

    if player_id is None:
        return False

    for season_id in list_seasons():
        players = load_players(season_id)

        for player in players:
            if player.get("id") == player_id:
                return True

    return False


def submit_comment(
    connection: sqlite3.Connection,
    *,
    comment_id: str,
    user_id: str,
    season_id: str,
    match_id: str,
    player_id: str,
    content: str,
    created_at: str,
    updated_at: str,
) -> str:
    if not is_supersonic_player(connection, user_id):
        raise ValueError("你没有社区互动权限")

    content = content.strip()
    if not content:
        raise ValueError("评论内容不能为空")
    if len(content) > 100:
        raise ValueError("评论内容不能超过 100 个字符")

    return create_comment_record(
        connection,
        comment_id=comment_id,
        user_id=user_id,
        season_id=season_id,
        match_id=match_id,
        player_id=player_id,
        content=content,
        created_at=created_at,
        updated_at=updated_at,
    )


def toggle_comment_like(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    comment_id: str,
    created_at: str,
) -> bool:
    if get_comment(connection, comment_id) is None:
        raise ValueError("评论不存在")
    if not is_supersonic_player(connection, user_id):
        raise ValueError("你没有社区互动权限")
    return toggle_comment_like_record(
        connection,
        user_id=user_id,
        comment_id=comment_id,
        created_at=created_at,
    )
