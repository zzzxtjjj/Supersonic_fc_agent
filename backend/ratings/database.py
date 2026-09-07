from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "app.db"

RATINGS_TABLE_SQL = """
CREATE TABLE ratings (
    id TEXT NOT NULL PRIMARY KEY,

    user_id TEXT NOT NULL,
    season_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    player_id TEXT NOT NULL,

    score REAL NOT NULL,
    reason TEXT,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    UNIQUE (
        user_id,
        match_id,
        player_id
    ),

    CHECK (
        score >= 0
        AND score <= 10
        AND ABS(score * 10 - ROUND(score * 10)) < 0.000001
    ),

    CHECK (
        reason IS NULL
        OR length(reason) <= 100
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
)
"""

RATING_LIKES_TABLE_SQL = """
CREATE TABLE rating_likes (
    user_id TEXT NOT NULL,
    rating_id TEXT NOT NULL,
    created_at TEXT NOT NULL,

    PRIMARY KEY (
        user_id,
        rating_id
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id),

    FOREIGN KEY (rating_id)
        REFERENCES ratings(id)
)
"""


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    if database_path is None:
        database_path = DB_PATH
    # FastAPI resolves synchronous dependencies in a worker thread and may use
    # the yielded connection in the async endpoint thread. The connection stays
    # request-scoped, so allowing that hand-off is safe and avoids SQLite's
    # default same-thread guard rejecting normal API requests.
    connection = sqlite3.connect(database_path, check_same_thread=False)

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def ensure_player_auth_schema(connection: sqlite3.Connection) -> None:
    """Create the additive Player Auth V1 tables without touching community data."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_credentials (
            user_id TEXT NOT NULL PRIMARY KEY,
            password_hash TEXT NOT NULL,
            activated_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS player_invites (
            id TEXT NOT NULL PRIMARY KEY,
            user_id TEXT NOT NULL,
            code_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS player_sessions (
            token_hash TEXT NOT NULL PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_invites_user_id "
        "ON player_invites(user_id)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_player_invites_one_open_per_user "
        "ON player_invites(user_id) WHERE used_at IS NULL"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_sessions_user_id "
        "ON player_sessions(user_id)"
    )


def init_database(database_path: str | Path = DB_PATH) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = get_connection(database_path)

    try:
        # 1. users
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                player_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )

        ensure_player_auth_schema(connection)

        # 2. season_rating_members
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS season_rating_members (
                season_id TEXT NOT NULL,
                user_id TEXT NOT NULL,

                PRIMARY KEY (season_id, user_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
            """
        )

        # 3. ratings
        connection.execute(
            RATINGS_TABLE_SQL.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
        )

        # 4. rating_likes
        connection.execute(
            RATING_LIKES_TABLE_SQL.replace(
                "CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1
            )
        )

        # 5. comment
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT NOT NULL PRIMARY KEY,

                user_id TEXT NOT NULL,
                season_id TEXT NOT NULL,
                match_id TEXT NOT NULL,
                player_id TEXT NOT NULL,

                content TEXT NOT NULL,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                CHECK (
                    length(trim(content)) >= 1
                    AND length(trim(content)) <= 100
                ),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
            """
        )

        # 6. comment_likes
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS comment_likes (
                user_id TEXT NOT NULL,
                comment_id TEXT NOT NULL,
                created_at TEXT NOT NULL,

                PRIMARY KEY (
                    user_id,
                    comment_id
                ),

                FOREIGN KEY (user_id)
                    REFERENCES users(id),

                FOREIGN KEY (comment_id)
                    REFERENCES comments(id)
            )
            """
        )


        connection.commit()
        migrate_half_step_rating_schema(connection)

    finally:
        connection.close()


def migrate_half_step_rating_schema(connection: sqlite3.Connection) -> bool:
    """Upgrade the old 0.5 score constraint to 0.1 without losing data."""

    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = ? AND name = ?",
        ("table", "ratings"),
    ).fetchone()
    if row is None:
        return False

    normalized_sql = " ".join(str(row[0]).split())
    if "score * 2 = CAST(score * 2 AS INTEGER)" not in normalized_sql:
        return False

    migration_table_sql = RATINGS_TABLE_SQL.replace(
        "CREATE TABLE ratings",
        "CREATE TABLE ratings_score_step_migration",
        1,
    )

    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(migration_table_sql)
        connection.execute(
            """
            INSERT INTO ratings_score_step_migration (
                id, user_id, season_id, match_id, player_id,
                score, reason, created_at, updated_at
            )
            SELECT
                id, user_id, season_id, match_id, player_id,
                score, reason, created_at, updated_at
            FROM ratings
            """
        )
        connection.execute("DROP TABLE ratings")
        connection.execute(
            "ALTER TABLE ratings_score_step_migration RENAME TO ratings"
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError("Rating score migration failed foreign-key validation.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")

    return True





def synchronize_empty_rating_schema(
    database_path: str | Path = DB_PATH,
) -> bool:
    """Align a legacy empty ratings table with the existing checked schema.

    A populated table is never rebuilt automatically, so real ratings and likes
    cannot be removed by initialization.
    """

    connection = get_connection(database_path)
    try:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", "ratings"),
        ).fetchone()
        if row is None:
            return False

        normalized_sql = " ".join(str(row[0]).split())
        if "ABS(score * 10 - ROUND(score * 10)) < 0.000001" in normalized_sql:
            return False

        rating_count = connection.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
        like_count = connection.execute("SELECT COUNT(*) FROM rating_likes").fetchone()[0]
        if rating_count or like_count:
            raise RuntimeError(
                "Legacy ratings schema contains data; automatic synchronization refused."
            )

        with connection:
            connection.execute("DROP TABLE rating_likes")
            connection.execute("DROP TABLE ratings")
            connection.execute(RATINGS_TABLE_SQL)
            connection.execute(RATING_LIKES_TABLE_SQL)
        return True
    finally:
        connection.close()


if __name__ == "__main__":
    init_database()
    print(f"Rating database initialized: {DB_PATH}")
