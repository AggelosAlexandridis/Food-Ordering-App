"""
Ghost test database bootstrap.

Import this module (before creating a DBManager) in any test that needs a
real DB connection. On first import per test run it creates an isolated
database from main.sql and points DBManager at it via the DATABASE env var,
so tests never read/write the real database configured in .env. Later
imports are no-ops (module-level code only runs once, Python caches it).
"""

import os
import re
from pathlib import Path

import mariadb
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT_DIR / "main.sql"
TEST_DATABASE = os.getenv("TEST_DATABASE", f"{os.getenv('DATABASE', 'ofd')}_test")


def _connect(database=None):
    return mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=database,
    )


def _strip_comments_and_db_selection(sql_text):
    # main.sql hardcodes `CREATE DATABASE ofd; use ofd;` and mixes '#'/'--'
    # comments (some containing literal ';', which would confuse the
    # statement splitter below) — drop both before splitting.
    lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if stripped.startswith("#") or stripped.startswith("--"):
            continue
        if re.match(r"(?i)^create database if not exists \w+;$", stripped):
            continue
        if re.match(r"(?i)^use \w+;$", stripped):
            continue
        lines.append(line)
    return "\n".join(lines)


def _split_sql_statements(sql_text):
    """Splits a .sql script into individual statements, honoring `delimiter`
    directives (used by main.sql to define triggers containing ';')."""
    delimiter = ";"
    buffer = ""
    statements = []
    for line in sql_text.splitlines():
        directive = re.match(r"(?i)^\s*delimiter\s+(\S+)\s*$", line)
        if directive:
            leftover = buffer.strip()
            if leftover:
                statements.append(leftover)
            buffer = ""
            delimiter = directive.group(1)
            continue

        buffer += line + "\n"
        stripped = buffer.rstrip()
        if delimiter != ";":
            # tolerate a stray ';' right after a custom delimiter (main.sql
            # has `end $$;`, where the trailing ';' is not itself a statement)
            stripped = stripped.rstrip(";").rstrip()
        if stripped.endswith(delimiter):
            statement = stripped[: -len(delimiter)].strip()
            if statement:
                statements.append(statement)
            buffer = ""

    leftover = buffer.strip()
    if leftover:
        statements.append(leftover)
    return statements


def _bootstrap_ghost_database():
    try:
        admin_conn = _connect()
        admin_cur = admin_conn.cursor()
        admin_cur.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE}")
        admin_cur.execute(f"CREATE DATABASE {TEST_DATABASE}")
        admin_conn.close()

        schema_sql = _strip_comments_and_db_selection(SCHEMA_FILE.read_text())
        schema_conn = _connect(database=TEST_DATABASE)
        schema_cur = schema_conn.cursor()
        for statement in _split_sql_statements(schema_sql):
            schema_cur.execute(statement)
        schema_conn.commit()
        schema_conn.close()
    except mariadb.Error as exc:
        raise RuntimeError(
            "Could not create the ghost test database "
            f"'{TEST_DATABASE}'. The app's DB user usually only has "
            "privileges on its own database. Ask an admin to run once:\n\n"
            f"  mariadb -u root -p -e \"CREATE DATABASE IF NOT EXISTS {TEST_DATABASE}; "
            f"GRANT ALL PRIVILEGES ON {TEST_DATABASE}.* TO '{os.getenv('DB_USER')}'@'%'; "
            "FLUSH PRIVILEGES;\"\n\n"
            f"Underlying error: {exc}"
        ) from exc

    os.environ["DATABASE"] = TEST_DATABASE


_bootstrap_ghost_database()
