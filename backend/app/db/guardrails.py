"""
Guardrails applied to every SQL string before it touches the database.

Defense in depth — three independent layers:
  1. This module (statement-type allow-listing + static checks)
  2. A DB role that only has SELECT privileges (see db/session.py + README)
  3. A statement_timeout set at the connection level

Any one of these failing shouldn't be catastrophic because the others
still hold.
"""
import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import DDL, DML, Keyword

# Only these statement "first tokens" are ever allowed to run.
_ALLOWED_DML = {"SELECT"}

# Hard-blocked keywords — if any of these appear anywhere in the
# (parsed, comment-stripped) query, it's rejected outright, regardless
# of statement type. Belt-and-suspenders against injected multi-statements.
_BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "GRANT", "REVOKE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REPLACE",
    "MERGE", "EXEC", "EXECUTE", "CALL",
}

_MULTI_STATEMENT_SEPARATOR = re.compile(r";\s*\S")  # semicolon followed by more content


class QueryRejected(Exception):
    """Raised when a candidate SQL query fails a guardrail check."""


def validate_query(raw_sql: str, max_rows: int, default_top_k: int) -> str:
    """
    Validate a candidate SQL query and return a (possibly LIMIT-adjusted)
    safe version of it. Raises QueryRejected if the query can't be made safe.
    """
    sql = raw_sql.strip().rstrip(";")

    if not sql:
        raise QueryRejected("Empty query.")

    if _MULTI_STATEMENT_SEPARATOR.search(sql):
        raise QueryRejected("Multiple statements in a single query are not allowed.")

    parsed = sqlparse.parse(sql)
    if len(parsed) != 1:
        raise QueryRejected("Query must be a single statement.")

    statement: Statement = parsed[0]
    stmt_type = statement.get_type()  # e.g. "SELECT", "UNKNOWN"

    if stmt_type != "SELECT":
        raise QueryRejected(f"Only SELECT statements are permitted (got: {stmt_type}).")

    upper_sql = sql.upper()
    for kw in _BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper_sql):
            raise QueryRejected(f"Disallowed keyword detected: {kw}")

    sql = _enforce_limit(sql, max_rows, default_top_k)
    return sql


def _enforce_limit(sql: str, max_rows: int, default_top_k: int) -> str:
    """
    Ensure the query has a LIMIT clause no larger than max_rows.
    If there's no LIMIT at all, add one using default_top_k.
    If there IS a LIMIT larger than max_rows, clamp it down.
    """
    match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
    if match:
        current_limit = int(match.group(1))
        if current_limit > max_rows:
            sql = sql[: match.start(1)] + str(max_rows) + sql[match.end(1):]
        return sql

    return f"{sql}\nLIMIT {min(default_top_k, max_rows)}"
