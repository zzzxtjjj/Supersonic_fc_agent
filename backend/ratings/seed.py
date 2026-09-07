import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.ratings.database import (
    DB_PATH,
    get_connection,
    init_database,
    synchronize_empty_rating_schema,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEASON_ID = "25-26"
DEFAULT_PLAYERS_PATH = (
    PROJECT_ROOT / "data" / "seasons" / DEFAULT_SEASON_ID / "players.json"
)
PLACEHOLDER_PLAYER_ID = "这里填张谢童甲在players.json里的真实id"
PLACEHOLDER_USER_ID = "user_zhang_xietongjia"


def _load_player_ids(players_path: Path) -> list[str]:
    payload = json.loads(players_path.read_text(encoding="utf-8"))
    players = payload.get("players")
    if not isinstance(players, list):
        raise ValueError(f"players must be a list: {players_path}")

    player_ids: list[str] = []
    for player in players:
        player_id = player.get("id") if isinstance(player, dict) else None
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError(f"player id is missing: {players_path}")
        player_ids.append(player_id)

    if len(player_ids) != len(set(player_ids)):
        raise ValueError(f"duplicate player id: {players_path}")
    return player_ids


def _delete_placeholder_rows(connection: sqlite3.Connection) -> dict[str, int]:
    deleted = {"users": 0, "memberships": 0, "ratings": 0, "likes": 0}

    cursor = connection.execute(
        """
        DELETE FROM rating_likes
        WHERE rating_id IN (
            SELECT id
            FROM ratings
            WHERE player_id = ?
               OR user_id IN (
                   SELECT id
                   FROM users
                   WHERE id = ? AND player_id = ?
               )
        )
        OR user_id IN (
            SELECT id
            FROM users
            WHERE id = ? AND player_id = ?
        )
        """,
        (
            PLACEHOLDER_PLAYER_ID,
            PLACEHOLDER_USER_ID,
            PLACEHOLDER_PLAYER_ID,
            PLACEHOLDER_USER_ID,
            PLACEHOLDER_PLAYER_ID,
        ),
    )
    deleted["likes"] = cursor.rowcount

    cursor = connection.execute(
        """
        DELETE FROM ratings
        WHERE player_id = ?
           OR user_id IN (
               SELECT id
               FROM users
               WHERE id = ? AND player_id = ?
           )
        """,
        (PLACEHOLDER_PLAYER_ID, PLACEHOLDER_USER_ID, PLACEHOLDER_PLAYER_ID),
    )
    deleted["ratings"] = cursor.rowcount

    cursor = connection.execute(
        """
        DELETE FROM season_rating_members
        WHERE user_id IN (
            SELECT id
            FROM users
            WHERE id = ? AND player_id = ?
        )
        """,
        (PLACEHOLDER_USER_ID, PLACEHOLDER_PLAYER_ID),
    )
    deleted["memberships"] = cursor.rowcount

    cursor = connection.execute(
        "DELETE FROM users WHERE id = ? AND player_id = ?",
        (PLACEHOLDER_USER_ID, PLACEHOLDER_PLAYER_ID),
    )
    deleted["users"] = cursor.rowcount
    return deleted


def seed_rating_members(
    database_path: str | Path = DB_PATH,
    players_path: str | Path = DEFAULT_PLAYERS_PATH,
    season_id: str = DEFAULT_SEASON_ID,
) -> dict[str, Any]:
    """Seed rating identities and season membership without touching real ratings."""

    database_path = Path(database_path)
    players_path = Path(players_path)
    player_ids = _load_player_ids(players_path)
    init_database(database_path)
    schema_synchronized = synchronize_empty_rating_schema(database_path)

    created_users = 0
    created_memberships = 0
    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection(database_path)
    try:
        with connection:
            deleted_placeholders = _delete_placeholder_rows(connection)

            for player_id in player_ids:
                row = connection.execute(
                    "SELECT id FROM users WHERE player_id = ?",
                    (player_id,),
                ).fetchone()
                if row is None:
                    user_id = f"user_{player_id}"
                    connection.execute(
                        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
                        (user_id, player_id, created_at),
                    )
                    created_users += 1
                else:
                    user_id = str(row[0])

                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO season_rating_members (season_id, user_id)
                    VALUES (?, ?)
                    """,
                    (season_id, user_id),
                )
                created_memberships += cursor.rowcount

        totals = {
            "users": connection.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "season_rating_members": connection.execute(
                "SELECT COUNT(*) FROM season_rating_members"
            ).fetchone()[0],
            "ratings": connection.execute("SELECT COUNT(*) FROM ratings").fetchone()[0],
            "rating_likes": connection.execute(
                "SELECT COUNT(*) FROM rating_likes"
            ).fetchone()[0],
        }
    finally:
        connection.close()

    return {
        "season_id": season_id,
        "player_count": len(player_ids),
        "created_users": created_users,
        "created_memberships": created_memberships,
        "schema_synchronized": schema_synchronized,
        "deleted_placeholders": deleted_placeholders,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Rating users and membership.")
    parser.add_argument("--database", type=Path, default=DB_PATH)
    parser.add_argument("--players", type=Path, default=DEFAULT_PLAYERS_PATH)
    parser.add_argument("--season", default=DEFAULT_SEASON_ID)
    args = parser.parse_args()
    result = seed_rating_members(args.database, args.players, args.season)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
