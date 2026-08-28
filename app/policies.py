import sqlite3
from datetime import datetime, timezone

DATABASE_PATH = "agent_registry.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_policy_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS governance_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            review_threshold REAL NOT NULL,
            block_threshold REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(name, version)
        )
        """
    )


def has_policy_version_constraint(connection):
    indexes = connection.execute(
        """
        PRAGMA index_list(governance_policies)
        """
    ).fetchall()

    for index in indexes:
        if index["unique"] != 1:
            continue

        index_name = index["name"].replace('"', '""')

        columns = connection.execute(
            f'PRAGMA index_info("{index_name}")'
        ).fetchall()

        column_names = [
            column["name"]
            for column in columns
        ]

        if column_names == ["name", "version"]:
            return True

    return False


def migrate_policy_table(connection):
    columns = connection.execute(
        """
        PRAGMA table_info(governance_policies)
        """
    ).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "version" in column_names:
        version_expression = "COALESCE(version, 1)"
    else:
        version_expression = "1"

    if "status" in column_names:
        status_expression = "status"
    else:
        status_expression = (
            "CASE "
            "WHEN active = 1 THEN 'ACTIVE' "
            "ELSE 'DRAFT' "
            "END"
        )

    if "approved_by" in column_names:
        approved_by_expression = "approved_by"
    else:
        approved_by_expression = "NULL"

    if "approved_at" in column_names:
        approved_at_expression = "approved_at"
    else:
        approved_at_expression = "NULL"

    connection.execute(
        """
        DROP TABLE IF EXISTS governance_policies_new
        """
    )

    connection.execute(
        """
        CREATE TABLE governance_policies_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            review_threshold REAL NOT NULL,
            block_threshold REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(name, version)
        )
        """
    )

    connection.execute(
        f"""
        INSERT INTO governance_policies_new (
            id,
            name,
            version,
            review_threshold,
            block_threshold,
            active,
            status,
            approved_by,
            approved_at,
            created_at
        )
        SELECT
            id,
            name,
            {version_expression},
            review_threshold,
            block_threshold,
            active,
            {status_expression},
            {approved_by_expression},
            {approved_at_expression},
            created_at
        FROM governance_policies
        """
    )

    connection.execute(
        """
        DROP TABLE governance_policies
        """
    )

    connection.execute(
        """
        ALTER TABLE governance_policies_new
        RENAME TO governance_policies
        """
    )


def init_policy_table():
    connection = get_connection()

    try:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'governance_policies'
            """
        ).fetchone()

        if table is None:
            create_policy_table(connection)

        elif not has_policy_version_constraint(connection):
            migrate_policy_table(connection)

        columns = connection.execute(
            """
            PRAGMA table_info(governance_policies)
            """
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "status" not in column_names:
            connection.execute(
                """
                ALTER TABLE governance_policies
                ADD COLUMN status TEXT
                NOT NULL DEFAULT 'DRAFT'
                """
            )

        if "approved_by" not in column_names:
            connection.execute(
                """
                ALTER TABLE governance_policies
                ADD COLUMN approved_by TEXT
                """
            )

        if "approved_at" not in column_names:
            connection.execute(
                """
                ALTER TABLE governance_policies
                ADD COLUMN approved_at TEXT
                """
            )

        connection.execute(
            """
            UPDATE governance_policies
            SET status = 'ACTIVE'
            WHERE active = 1
            """
        )

        existing = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM governance_policies
            """
        ).fetchone()

        if existing["count"] == 0:
            now = datetime.now(
                timezone.utc
            ).isoformat()

            connection.execute(
                """
                INSERT INTO governance_policies (
                    name,
                    version,
                    review_threshold,
                    block_threshold,
                    active,
                    status,
                    approved_by,
                    approved_at,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "default-risk-policy",
                    1,
                    0.5,
                    0.8,
                    1,
                    "ACTIVE",
                    "system-bootstrap",
                    now,
                    now,
                ),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_policy(
    name: str,
    review_threshold: float,
    block_threshold: float,
):
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM governance_policies
            WHERE name = ?
            LIMIT 1
            """,
            (name,),
        ).fetchone()

        if existing is not None:
            raise ValueError(
                f"Policy '{name}' already exists. "
                "Create a new version instead."
            )

        cursor = connection.execute(
            """
            INSERT INTO governance_policies (
                name,
                version,
                review_threshold,
                block_threshold,
                active,
                status,
                approved_by,
                approved_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                1,
                review_threshold,
                block_threshold,
                0,
                "DRAFT",
                None,
                None,
                datetime.now(
                    timezone.utc
                ).isoformat(),
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        connection.commit()

        return dict(row)

    except sqlite3.IntegrityError as exc:
        connection.rollback()

        raise ValueError(
            f"Policy '{name}' already exists."
        ) from exc

    except ValueError:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_policy_version(
    policy_id: int,
    review_threshold: float,
    block_threshold: float,
):
    connection = get_connection()

    try:
        connection.execute(
            """
            BEGIN IMMEDIATE
            """
        )

        source_policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if source_policy is None:
            connection.rollback()
            return None

        latest_version = connection.execute(
            """
            SELECT MAX(version) AS version
            FROM governance_policies
            WHERE name = ?
            """,
            (source_policy["name"],),
        ).fetchone()

        next_version = (
            latest_version["version"] + 1
        )

        cursor = connection.execute(
            """
            INSERT INTO governance_policies (
                name,
                version,
                review_threshold,
                block_threshold,
                active,
                status,
                approved_by,
                approved_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_policy["name"],
                next_version,
                review_threshold,
                block_threshold,
                0,
                "DRAFT",
                None,
                None,
                datetime.now(
                    timezone.utc
                ).isoformat(),
            ),
        )

        new_policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        connection.commit()

        return dict(new_policy)

    except sqlite3.IntegrityError as exc:
        connection.rollback()

        raise ValueError(
            "Unable to create policy version."
        ) from exc

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def approve_policy(
    policy_id: int,
    approved_by: str,
):
    connection = get_connection()

    try:
        connection.execute(
            """
            BEGIN IMMEDIATE
            """
        )

        policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if policy is None:
            connection.rollback()
            return None

        if policy["status"] != "DRAFT":
            raise ValueError(
                "Only DRAFT policies can be approved. "
                f"Current status is {policy['status']}."
            )

        approved_at = datetime.now(
            timezone.utc
        ).isoformat()

        connection.execute(
            """
            UPDATE governance_policies
            SET
                status = 'APPROVED',
                approved_by = ?,
                approved_at = ?
            WHERE id = ?
            """,
            (
                approved_by,
                approved_at,
                policy_id,
            ),
        )

        approved_policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        connection.commit()

        return dict(approved_policy)

    except ValueError:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

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
            ORDER BY name ASC, version DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_policy_versions(policy_id: int):
    connection = get_connection()

    try:
        policy = connection.execute(
            """
            SELECT name
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if policy is None:
            return None

        rows = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE name = ?
            ORDER BY version DESC
            """,
            (policy["name"],),
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
              AND status = 'ACTIVE'
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
        connection.execute(
            """
            BEGIN IMMEDIATE
            """
        )

        policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        if policy is None:
            connection.rollback()
            return None

        if (
            policy["status"] == "ACTIVE"
            and policy["active"] == 1
        ):
            connection.commit()
            return dict(policy)

        if policy["status"] != "APPROVED":
            raise ValueError(
                "Only APPROVED policies can be "
                "activated. "
                f"Current status is {policy['status']}."
            )

        connection.execute(
            """
            UPDATE governance_policies
            SET
                active = 0,
                status = 'APPROVED'
            WHERE active = 1
               OR status = 'ACTIVE'
            """
        )

        connection.execute(
            """
            UPDATE governance_policies
            SET
                active = 1,
                status = 'ACTIVE'
            WHERE id = ?
            """,
            (policy_id,),
        )

        activated_policy = connection.execute(
            """
            SELECT *
            FROM governance_policies
            WHERE id = ?
            """,
            (policy_id,),
        ).fetchone()

        connection.commit()

        return dict(activated_policy)

    except ValueError:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


init_policy_table()