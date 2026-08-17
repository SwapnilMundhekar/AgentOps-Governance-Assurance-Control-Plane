import sqlite3

DB_PATH = "agent_registry.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            version TEXT NOT NULL,
            manifest_path TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def register_agent(name: str, version: str, manifest_path: str):
    conn = sqlite3.connect(DB_PATH)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agents (name, version, manifest_path)
            VALUES (?, ?, ?)
        """, (name, version, manifest_path))

        conn.commit()

        return {
            "registered": True,
            "name": name,
            "version": version
        }

    except sqlite3.IntegrityError:
        return {
            "registered": False,
            "error": f"Agent '{name}' already exists"
        }

    finally:
        conn.close()