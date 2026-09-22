"""
Tools exposed to the agent. We reuse LangChain's SQLDatabase for schema
introspection, but replace the raw "run query" tool with a guarded version
that runs every candidate query through app.db.guardrails first.
"""
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
)
from langchain_core.tools import tool

from app.core.config import get_settings
from app.db.guardrails import QueryRejected, validate_query
from app.db.session import get_sql_database

_settings = get_settings()


def build_tools():
    _db = get_sql_database()  # fresh reflect each call — sees newly uploaded tables
    list_tables_tool = ListSQLDatabaseTool(db=_db)
    schema_tool = InfoSQLDatabaseTool(db=_db)

    @tool
    def run_guarded_sql_query(query: str) -> str:
        """
        Execute a READ-ONLY SQL query against the database and return the
        results. The query MUST be a single SELECT statement. It will be
        rejected if it contains any write/DDL keywords, multiple statements,
        or a LIMIT larger than what's allowed. If rejected, fix the query
        based on the error message and try again.
        """
        try:
            safe_sql = validate_query(
                query,
                max_rows=_settings.max_rows_returned,
                default_top_k=_settings.default_top_k,
            )
        except QueryRejected as e:
            return f"QUERY REJECTED by guardrails: {e}. Rewrite the query and try again."

        try:
            result = _db.run(safe_sql, include_columns=True)
        except Exception as e:
            return f"SQL ERROR: {e}. Check the schema and rewrite the query."

        return result

    return [list_tables_tool, schema_tool, run_guarded_sql_query]
