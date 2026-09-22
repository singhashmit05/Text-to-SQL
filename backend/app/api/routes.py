from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.agent.graph import build_agent
from app.core.config import get_settings
from app.db.loader import UploadRejected, load_dataset
from app.db.session import get_admin_engine, get_sql_database

router = APIRouter()
_settings = get_settings()

# The role name the agent connects as — extracted from DATABASE_URL's
# username so the upload endpoint knows who to GRANT new tables to.
_raw_username = _settings.database_url.split("://", 1)[1].split(":", 1)[0]
_AGENT_ROLE = _raw_username.split(".")[0]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    steps: list[dict]  # tool calls the agent made, for a "show your work" UI


class UploadResult(BaseModel):
    table_name: str
    row_count: int
    columns: list[str]


class UploadResponse(BaseModel):
    results: list[UploadResult]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/schema")
def schema():
    """Lets the frontend show the user what tables/columns exist."""
    try:
        db = get_sql_database()
        return {"tables": db.get_usable_table_names(), "info": db.get_table_info()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        db = get_sql_database()  # fresh reflect — sees any newly uploaded tables
        agent = build_agent(dialect=db.dialect)
        result = agent.invoke({"messages": [{"role": "user", "content": req.question}]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    messages = result.get("messages", [])
    final_message = messages[-1] if messages else None
    raw_answer = getattr(final_message, "content", "") if final_message else ""
    
    if isinstance(raw_answer, list):
        answer = "".join(part.get("text", "") for part in raw_answer if isinstance(part, dict) and "text" in part)
    elif not isinstance(raw_answer, str):
        answer = str(raw_answer)
    else:
        answer = raw_answer

    steps = []
    for m in messages:
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                steps.append({"tool": tc.get("name"), "args": tc.get("args")})

    return QueryResponse(answer=answer, steps=steps)


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(files: list[UploadFile] = File(...)):
    """
    Accepts CSV/Excel files, creates tables from them, grants the query agent's 
    read-only role access to them, and returns a summary.
    """
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    results = []
    for file in files:
        raw_bytes = await file.read()
        try:
            result = load_dataset(
                filename=file.filename or "upload.csv",
                raw_bytes=raw_bytes,
                admin_engine=get_admin_engine(),
                agent_role=_AGENT_ROLE,
            )
            results.append(UploadResult(**result))
        except UploadRejected as e:
            raise HTTPException(status_code=400, detail=f"Error in {file.filename}: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed for {file.filename}: {e}")

    return UploadResponse(results=results)
