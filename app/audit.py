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


def get_audit_records(limit: int = 50):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                agent_id,
                action,
                risk_score,
                decision,
                reason,
                created_at
            FROM governance_audit
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


init_audit_table()