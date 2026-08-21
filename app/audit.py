import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = "agent_registry.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_audit_table():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governance_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                risk_score REAL NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def log_governance_decision(
    agent_id: str,
    action: str,
    risk_score: float,
    decision: str,
    reason: str,
):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO governance_audit (
                agent_id,
                action,
                risk_score,
                decision,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                action,
                risk_score,
                decision,
                reason,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_audit_records(
    limit: int = 50,
    agent_id: str | None = None,
    decision: str | None = None,
):
    connection = get_connection()

    try:
        query = """
            SELECT
                id,
                agent_id,
                action,
                risk_score,
                decision,
                reason,
                created_at
            FROM governance_audit
            WHERE 1 = 1
        """

        parameters = []

        if agent_id is not None:
            query += " AND agent_id = ?"
            parameters.append(agent_id)

        if decision is not None:
            query += " AND decision = ?"
            parameters.append(decision)

        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit)

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


init_audit_table()