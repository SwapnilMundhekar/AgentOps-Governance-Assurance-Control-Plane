import sqlite3
from datetime import datetime, timezone

DB_PATH = "agent_registry.db"


def init_audit_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS governance_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            action TEXT NOT NULL,
            risk_score REAL NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            requires_human_review INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def log_governance_decision(
    agent_id,
    action,
    risk_score,
    decision,
    reason,
    requires_human_review
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO governance_audit (
            timestamp,
            agent_id,
            action,
            risk_score,
            decision,
            reason,
            requires_human_review
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        agent_id,
        action,
        risk_score,
        decision,
        reason,
        int(requires_human_review)
    ))

    conn.commit()
    conn.close()