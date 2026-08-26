import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = "agent_registry.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_policy_table():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governance_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                review_threshold REAL NOT NULL,
                block_threshold REAL NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        columns = connection.execute(
            """
            PRAGMA table_info(governance_policies)
            """
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "version" not in column_names:
            connection.execute(
                """
                ALTER TABLE governance_policies
                ADD COLUMN version INTEGER NOT NULL DEFAULT 1
                """
            )

        existing = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM governance_policies
            """
        ).fetchone()

        if existing["count"] == 0:
            connection.execute(
                """
                INSERT INTO governance_policies (
                    name,
                    version,
                    review_threshold,
                    block_threshold,
                    active,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "default-risk-policy",
                    1,
                    0.5,
                    0.8,
                    1,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        connection.commit()

    finally:
        connection.close()


def create_policy(
    name: str,
    review_threshold: float,
    block_threshold: float,
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO governance_policies (
                name,
                version,
                review_threshold,
                block_threshold,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                1,
                review_threshold,
                block_threshold,
                0,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()

        return get_policy(cursor.lastrowid)

    except sqlite3.IntegrityError as exc:
        raise ValueError(
            f"Policy '{name}' already exists."
        ) from exc

    finally:
        connection.close()


def get_policy(policy_id: int):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_policies():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM governance_policies
            ORDER BY id DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_active_policy():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def activate_policy(policy_id: int):
    connection = get_connection()

    try:
        policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if policy is None:
            return None

        connection.execute(
            """
            UPDATE governance_policies
            SET active = 0
            """
        )

        connection.execute(
            """
            UPDATE governance_policies
            SET active = 1
            WHERE id = ?
            """,
            (policy_id,),
        )

        connection.commit()

    finally:
        connection.close()

    return get_policy(policy_id)


init_policy_table()