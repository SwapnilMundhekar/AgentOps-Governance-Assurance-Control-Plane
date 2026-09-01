import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = "agent_registry.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_agent_table():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                owner TEXT NOT NULL,
                purpose TEXT NOT NULL,
                risk_tier TEXT NOT NULL DEFAULT 'MEDIUM',
                status TEXT NOT NULL DEFAULT 'REGISTERED',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(agent_id, version),
                CHECK (
                    risk_tier IN (
                        'LOW',
                        'MEDIUM',
                        'HIGH',
                        'CRITICAL'
                    )
                ),
                CHECK (
                    status IN (
                        'REGISTERED',
                        'SUSPENDED',
                        'RETIRED'
                    )
                )
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def register_agent_record(
    agent_id: str,
    name: str,
    version: str,
    owner: str,
    purpose: str,
    risk_tier: str,
):
    connection = get_connection()

    try:
        now = datetime.now(
            timezone.utc
        ).isoformat()

        cursor = connection.execute(
            """
            INSERT INTO agents (
                agent_id,
                name,
                version,
                owner,
                purpose,
                risk_tier,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                name,
                version,
                owner,
                purpose,
                risk_tier,
                "REGISTERED",
                now,
                now,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        connection.commit()

        return dict(row)

    except sqlite3.IntegrityError as exc:
        connection.rollback()

        raise ValueError(
            f"Agent '{agent_id}' version "
            f"'{version}' is already registered."
        ) from exc

    finally:
        connection.close()


def get_agents(
    limit: int = 50,
    status: str | None = None,
    risk_tier: str | None = None,
):
    connection = get_connection()

    try:
        query = """
            SELECT *
            FROM agents
            WHERE 1 = 1
        """

        parameters = []

        if status is not None:
            query += " AND status = ?"
            parameters.append(status)

        if risk_tier is not None:
            query += " AND risk_tier = ?"
            parameters.append(risk_tier)

        query += """
            ORDER BY id DESC
            LIMIT ?
        """

        parameters.append(limit)

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_agent_versions(
    agent_id: str,
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM agents
            WHERE agent_id = ?
            ORDER BY id DESC
            """,
            (agent_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_latest_agent(
    agent_id: str,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM agents
            WHERE agent_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (agent_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def update_latest_agent_status(
    agent_id: str,
    new_status: str,
):
    valid_statuses = {
        "REGISTERED",
        "SUSPENDED",
        "RETIRED",
    }

    if new_status not in valid_statuses:
        raise ValueError(
            f"Invalid agent status: {new_status}"
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            BEGIN IMMEDIATE
            """
        )

        agent = connection.execute(
            """
            SELECT *
            FROM agents
            WHERE agent_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (agent_id,),
        ).fetchone()

        if agent is None:
            connection.rollback()
            return None

        current_status = agent["status"]

        if current_status == new_status:
            connection.commit()
            return dict(agent)

        if current_status == "RETIRED":
            raise ValueError(
                "A RETIRED agent version cannot "
                "be reactivated or suspended."
            )

        if (
            new_status == "REGISTERED"
            and current_status != "SUSPENDED"
        ):
            raise ValueError(
                "Only a SUSPENDED agent can "
                "be reactivated."
            )

        if (
            new_status == "SUSPENDED"
            and current_status != "REGISTERED"
        ):
            raise ValueError(
                "Only a REGISTERED agent can "
                "be suspended."
            )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        connection.execute(
            """
            UPDATE agents
            SET
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                now,
                agent["id"],
            ),
        )

        updated_agent = connection.execute(
            """
            SELECT *
            FROM agents
            WHERE id = ?
            """,
            (agent["id"],),
        ).fetchone()

        connection.commit()

        return dict(updated_agent)

    except ValueError:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


init_agent_table()