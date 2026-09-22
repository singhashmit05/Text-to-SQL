"""
Builds the text-to-SQL agent.

Workflow the agent follows (enforced via the system prompt, not hard-coded
control flow, since create_agent lets the model decide tool order):

  1. Discover  - list_sql_database_tool
  2. Inspect   - info_sql_database_tool (schema + sample rows)
  3. Generate  - the model writes SQL
  4. Validate  - run_guarded_sql_query rejects unsafe SQL before running it
  5. Execute   - run_guarded_sql_query runs it
  6. Retry     - on error/rejection, the model rewrites and retries
  7. Format    - the model turns rows into a plain-English answer
"""
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from app.agent.tools import build_tools
from app.core.config import get_settings

_settings = get_settings()

SYSTEM_PROMPT = """You are a careful data analyst that answers questions by \
querying a SQL database.

Dialect: {dialect}
Default row limit if the user doesn't ask for a specific number: {top_k}

Rules:
- ALWAYS call the schema/list tools before writing SQL for a table you \
haven't inspected yet in this conversation.
- Only ever write a single SELECT statement. Never attempt INSERT, UPDATE, \
DELETE, DROP, ALTER, or any other write/DDL operation — those will be \
rejected and wasted a turn.
- If a query is rejected or errors, read the message, fix the query, and \
try again. You have a limited number of retries, so think carefully rather \
than guessing repeatedly.
- After getting results, answer the user's question in plain English. \
Mention the key numbers. Don't just dump a raw table unless asked to.
- If you cannot answer safely or the data doesn't support the question, say \
so clearly instead of fabricating a number.
"""


def build_agent(dialect: str):
    model = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=_settings.groq_api_key,
        temperature=0,
    )
    tools = build_tools()
    system_prompt = SYSTEM_PROMPT.format(
        dialect=dialect,
        top_k=_settings.default_top_k,
    )
    return create_agent(model=model, tools=tools, system_prompt=system_prompt)
