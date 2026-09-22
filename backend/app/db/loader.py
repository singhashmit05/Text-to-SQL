"""
Lets a user upload their own CSV/Excel file and turns it into a real
Postgres table the agent can query.

Flow:
  1. Parse the file into a pandas DataFrame.
  2. Sanitize the table name + column names (untrusted input — the
     filename and header row come straight from the user).
  3. Write the table using the ADMIN connection (has CREATE/INSERT —
     the agent's own connection never does).
  4. GRANT SELECT on just this new table to sql_agent_ro, so the agent
     can query it going forward.

This path is intentionally separate from app/agent/tools.py — the LLM
never touches the admin connection, and this code never runs SQL that
came from the LLM. It only runs pandas' own parameterized to_sql().
"""
import re
import uuid

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import get_settings

_settings = get_settings()

_ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
_IDENTIFIER_RE = re.compile(r"[^a-z0-9_]")


class UploadRejected(Exception):
    pass


def _sanitize_identifier(raw: str, fallback_prefix: str = "col") -> str:
    """Turn arbitrary user-provided text into a safe Postgres identifier."""
    name = raw.strip().lower().replace(" ", "_")
    name = _IDENTIFIER_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name or not name[0].isalpha():
        name = f"{fallback_prefix}_{name}" if name else f"{fallback_prefix}_{uuid.uuid4().hex[:6]}"
    return name[:63]  # Postgres identifier length limit


def _read_dataframe(filename: str, raw_bytes: bytes) -> pd.DataFrame:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise UploadRejected(f"Unsupported file type '.{ext}'. Use CSV or Excel (.csv, .xlsx, .xls).")

    import io
    buffer = io.BytesIO(raw_bytes)

    try:
        if ext == "csv":
            df = pd.read_csv(buffer)
        else:
            df = pd.read_excel(buffer)
    except Exception as e:
        raise UploadRejected(f"Could not parse file: {e}")

    if df.empty:
        raise UploadRejected("The file has no rows.")

    if len(df) > _settings.max_upload_rows:
        raise UploadRejected(
            f"File has {len(df)} rows, which exceeds the limit of "
            f"{_settings.max_upload_rows}. Trim it and try again."
        )

    return df


def load_dataset(
    filename: str,
    raw_bytes: bytes,
    admin_engine: Engine,
    agent_role: str,
    table_name_hint: str | None = None,
) -> dict:
    """
    Parses the uploaded file and creates a Postgres table from it.
    Returns a summary dict: {table_name, row_count, columns}.
    """
    size_mb = len(raw_bytes) / (1024 * 1024)
    if size_mb > _settings.max_upload_mb:
        raise UploadRejected(f"File is {size_mb:.1f} MB, which exceeds the {_settings.max_upload_mb} MB limit.")

    df = _read_dataframe(filename, raw_bytes)

    # Table name: from the hint if given, else the filename (minus extension).
    base_name = table_name_hint or filename.rsplit(".", 1)[0]
    table_name = _sanitize_identifier(base_name, fallback_prefix="uploaded")

    # Sanitize + de-duplicate column names.
    seen = {}
    safe_columns = []
    for col in df.columns:
        safe = _sanitize_identifier(str(col))
        if safe in seen:
            seen[safe] += 1
            safe = f"{safe}_{seen[safe]}"
        else:
            seen[safe] = 0
        safe_columns.append(safe)
    df.columns = safe_columns

    # Write the table. if_exists="replace" — re-uploading the same name
    # overwrites it, which is the expected behavior for this feature.
    df.to_sql(table_name, admin_engine, if_exists="replace", index=False, method="multi", chunksize=1000)

    # Grant the read-only agent role access to exactly this table.
    with admin_engine.begin() as conn:
        conn.execute(text(f'GRANT SELECT ON "{table_name}" TO "{agent_role}"'))

    return {
        "table_name": table_name,
        "row_count": len(df),
        "columns": list(df.columns),
    }
