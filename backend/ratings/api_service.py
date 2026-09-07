import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from backend.api.season_data import (
    calculate_match_player_stats,
    find_match_record,
    find_player,
    load_players,
    team_map,
)
from backend.ratings.repository import (
    count_comment_likes,
    count_rating_likes,
    get_comment,
    get_comments_for_player_match,
    get_match_ratings,
    get_rating,
    get_user_player_id,
    get_user_rating_for_player_match,
    is_comment_liked_by_user,
    is_rating_liked_by_user,
    is_rating_member,
)
from backend.ratings.service import (
    is_supersonic_player,
    submit_comment,
    submit_rating,
    toggle_comment_like,
    toggle_rating_like,
)


class RatingTargetNotFound(ValueError):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _match_context(match_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    match = find_match_record(match_id)
    if match is None:
        raise RatingTargetNotFound(f"Match not found: {match_id}")
    return match, load_players(match["season"])


def _require_player(
    players: list[dict[str, Any]],
    player_id: str,
) -> dict[str, Any]:
    player = next((item for item in players if item["id"] == player_id), None)
    if player is None:
        raise RatingTargetNotFound(f"Player not found in match season: {player_id}")
    return player


def _author(connection: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    player_id = get_user_player_id(connection, user_id)
    if player_id is None:
        return {"player_id": user_id, "name": user_id, "photo_url": None}
    identity = find_player(player_id)
    if identity is None:
        return {"player_id": player_id, "name": player_id, "photo_url": None}
    player = identity["player"]
    return {
        "player_id": player_id,
        "name": player["name"],
        "photo_url": player.get("photo_url"),
    }


def _comment_response(
    connection: sqlite3.Connection,
    row: sqlite3.Row | tuple[Any, ...],
    viewer_user_id: str | None,
) -> dict[str, Any]:
    comment_id = str(row[0])
    return {
        "id": comment_id,
        "author": _author(connection, str(row[1])),
        "content": str(row[5]),
        "like_count": count_comment_likes(connection, comment_id),
        "liked_by_me": bool(
            viewer_user_id
            and is_comment_liked_by_user(connection, viewer_user_id, comment_id)
        ),
        "created_at": str(row[6]),
        "updated_at": str(row[7]),
    }


def list_player_comments(
    connection: sqlite3.Connection,
    *,
    match_id: str,
    player_id: str,
    viewer_user_id: str | None,
) -> list[dict[str, Any]]:
    match, players = _match_context(match_id)
    del match
    _require_player(players, player_id)
    rows = get_comments_for_player_match(connection, match_id, player_id)
    rows = sorted(rows, key=lambda row: (str(row[7]), str(row[0])), reverse=True)
    return [_comment_response(connection, row, viewer_user_id) for row in rows]


def _player_rating(
    connection: sqlite3.Connection,
    *,
    match_id: str,
    player_id: str,
    viewer_user_id: str | None,
    match_ratings: list[sqlite3.Row | tuple[Any, ...]],
) -> dict[str, Any]:
    rows = [row for row in match_ratings if str(row[4]) == player_id]
    count = len(rows)
    average = round(sum(float(row[5]) for row in rows) / count, 2) if count else None
    mine = (
        get_user_rating_for_player_match(
            connection,
            viewer_user_id,
            match_id,
            player_id,
        )
        if viewer_user_id
        else None
    )
    reasons = []
    for row in sorted(rows, key=lambda item: (str(item[8]), str(item[0])), reverse=True):
        reason = row[6]
        if reason is None:
            continue
        rating_id = str(row[0])
        reasons.append(
            {
                "id": rating_id,
                "author": _author(connection, str(row[1])),
                "score": float(row[5]),
                "reason": str(reason),
                "like_count": count_rating_likes(connection, rating_id),
                "liked_by_me": bool(
                    viewer_user_id
                    and is_rating_liked_by_user(
                        connection,
                        viewer_user_id,
                        rating_id,
                    )
                ),
                "updated_at": str(row[8]),
            }
        )
    return {
        "average": average,
        "count": count,
        "my_score": float(mine[5]) if mine is not None else None,
        "my_reason": mine[6] if mine is not None else None,
        "reasons": reasons,
    }


def get_rating_match_page(
    connection: sqlite3.Connection,
    *,
    match_id: str,
    viewer_user_id: str | None,
) -> dict[str, Any]:
    match, players = _match_context(match_id)
    season = match["season"]
    teams = team_map(season)
    facts_by_player = calculate_match_player_stats(match)
    match_ratings = get_match_ratings(connection, match_id)
    authenticated = viewer_user_id is not None
    verified_player = bool(
        viewer_user_id and is_supersonic_player(connection, viewer_user_id)
    )
    can_rate = bool(
        viewer_user_id and is_rating_member(connection, viewer_user_id, season)
    )

    player_items: list[dict[str, Any]] = []
    for player in players:
        player_id = player["id"]
        comments = list_player_comments(
            connection,
            match_id=match_id,
            player_id=player_id,
            viewer_user_id=viewer_user_id,
        )
        top_comment = None
        if comments:
            top_comment = max(
                comments,
                key=lambda item: (
                    item["like_count"],
                    item["updated_at"],
                    item["id"],
                ),
            )
        rating = _player_rating(
            connection,
            match_id=match_id,
            player_id=player_id,
            viewer_user_id=viewer_user_id,
            match_ratings=match_ratings,
        )
        player_items.append(
            {
                "player_id": player_id,
                "name": player["name"],
                "number": player.get("season_data", {}).get("number"),
                "photo_url": player.get("photo_url"),
                "match_facts": facts_by_player.get(
                    player_id,
                    {"goals": 0, "assists": 0},
                ),
                "rating": rating,
                "top_comment": top_comment,
                "comment_count": len(comments),
            }
        )

    mvp_candidates = [item for item in player_items if item["rating"]["count"] >= 3]
    mvp_candidates.sort(
        key=lambda item: (
            -item["rating"]["average"],
            -item["rating"]["count"],
            item["player_id"],
        )
    )
    fan_mvp = None
    if mvp_candidates:
        winner = mvp_candidates[0]
        fan_mvp = {
            "player_id": winner["player_id"],
            "name": winner["name"],
            "photo_url": winner["photo_url"],
            "average": winner["rating"]["average"],
            "rating_count": winner["rating"]["count"],
        }

    home = teams[match["home_team_id"]]
    away = teams[match["away_team_id"]]
    return {
        "match": {
            "id": match["id"],
            "season_id": season,
            "competition": match["competition"],
            "round": match.get("round"),
            "date": match.get("date"),
            "home_team": {
                "id": home["id"],
                "name": home["name"],
                "crest_url": home.get("crest_url"),
            },
            "away_team": {
                "id": away["id"],
                "name": away["name"],
                "crest_url": away.get("crest_url"),
            },
            "home_score": match["home_score"],
            "away_score": match["away_score"],
        },
        "viewer": {
            "authenticated": authenticated,
            "is_supersonic_player": verified_player,
            "can_rate": can_rate,
            "can_comment": verified_player,
            "can_like": verified_player,
        },
        "fan_mvp": fan_mvp,
        "players": player_items,
    }


def put_rating(
    connection: sqlite3.Connection,
    *,
    match_id: str,
    player_id: str,
    user_id: str,
    score: float,
    reason: str | None,
) -> dict[str, Any]:
    match, players = _match_context(match_id)
    _require_player(players, player_id)
    timestamp = _now()
    rating_id = submit_rating(
        connection,
        rating_id=f"rating_{uuid.uuid4().hex}",
        user_id=user_id,
        season_id=match["season"],
        match_id=match_id,
        player_id=player_id,
        score=score,
        reason=reason,
        created_at=timestamp,
        updated_at=timestamp,
    )
    row = get_rating(connection, rating_id)
    rating = _player_rating(
        connection,
        match_id=match_id,
        player_id=player_id,
        viewer_user_id=user_id,
        match_ratings=get_match_ratings(connection, match_id),
    )
    return {
        "rating_id": rating_id,
        "score": float(row[5]),
        "reason": row[6],
        "average": rating["average"],
        "rating_count": rating["count"],
    }


def post_comment(
    connection: sqlite3.Connection,
    *,
    match_id: str,
    player_id: str,
    user_id: str,
    content: str,
) -> dict[str, Any]:
    match, players = _match_context(match_id)
    _require_player(players, player_id)
    timestamp = _now()
    comment_id = submit_comment(
        connection,
        comment_id=f"comment_{uuid.uuid4().hex}",
        user_id=user_id,
        season_id=match["season"],
        match_id=match_id,
        player_id=player_id,
        content=content,
        created_at=timestamp,
        updated_at=timestamp,
    )
    return _comment_response(
        connection,
        get_comment(connection, comment_id),
        user_id,
    )


def post_rating_like(
    connection: sqlite3.Connection,
    *,
    rating_id: str,
    user_id: str,
) -> dict[str, Any]:
    liked = toggle_rating_like(
        connection,
        user_id=user_id,
        rating_id=rating_id,
        created_at=_now(),
    )
    return {"liked": liked, "like_count": count_rating_likes(connection, rating_id)}


def post_comment_like(
    connection: sqlite3.Connection,
    *,
    comment_id: str,
    user_id: str,
) -> dict[str, Any]:
    liked = toggle_comment_like(
        connection,
        user_id=user_id,
        comment_id=comment_id,
        created_at=_now(),
    )
    return {
        "liked": liked,
        "like_count": count_comment_likes(connection, comment_id),
    }
