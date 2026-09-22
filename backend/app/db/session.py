"""
Database engine setup.

IMPORTANT (guardrail layer 2): `database_url` in your .env should point to
a Postgres role that ONLY has SELECT granted, e.g.:

    CREATE ROLE sql_agent_ro LOGIN PASSWORD '...';
    GRANT CONNECT ON DATABASE yourdb TO sql_agent_ro;
    GRANT USAGE ON SCHEMA public TO sql_agent_ro;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_agent_ro;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_agent_ro;

That way, even if every application-level guardrail were somehow bypassed,
the database itself would refuse any write.
"""
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, event

from app.core.config import get_settings

_settings = get_settings()

_engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)


@event.listens_for(_engine, "connect")
def _set_statement_timeout(dbapi_connection, connection_record):
    """Apply a per-connection statement_timeout (Postgres) so a runaway
    query the agent generates can never hang the API."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET statement_timeout = {_settings.query_timeout_seconds * 1000}")
        cursor.close()
    except Exception:
        # Non-Postgres backends (e.g. sqlite in local dev) don't support this.
        pass


def get_sql_database() -> SQLDatabase:
    """Returns a LangChain SQLDatabase wrapper bound to the read-only engine.
    Built fresh each call (cheap) so newly uploaded tables show up immediately
    without needing a cache-invalidation step."""
    return SQLDatabase(
        engine=_engine,
        sample_rows_in_table_info=3,
    )


# --- Admin engine — used ONLY by app/db/loader.py for creating tables from
# uploaded datasets. NEVER imported by the agent/tools code path. ---
_admin_engine = create_engine(
    _settings.database_admin_url,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=2,
)


def get_admin_engine():
    return _admin_engine
