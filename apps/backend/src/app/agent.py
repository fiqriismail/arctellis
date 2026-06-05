from __future__ import annotations

import logging
from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings
from app.services.sharepoint import SharePointService
from app.tools.list_tools import make_tools

logger = logging.getLogger(__name__)

_SCHEMA_DOC = Path(__file__).parent / "data" / "sharepoint_schema.md"

_BASE_PROMPT = """\
You are an assistant that answers questions about a SharePoint list.

Guidelines:
- The list schema is provided below — use it to identify the correct internal
  column names before querying. Only call get_schema if the schema section is
  absent or you need to confirm a column exists.
- Use only the provided tools to fetch data — never fabricate column names or
  values.
- All arithmetic is performed by the tools; never compute numbers yourself.
- If a question is ambiguous or references a column that does not exist, ask a
  clarifying question rather than guessing.
- If a question is unrelated to the SharePoint list, politely decline to answer.
- Always answer in plain English. Do not echo raw JSON or tool output directly
  to the user.

Data conventions:
- Person/people columns (type 'person') are returned as objects with two keys:
    - "LookupValue": the person's display name (e.g. "John Doe")
    - "Email": their email address (may be absent on some columns)
- Person/people columns CANNOT be used in an odata_filter — they store a hidden
  user id (not the display name) and are usually not indexed, so an OData filter
  on them fails or never matches. To find rows by a person's name or email, call
  filter_rows with NO odata_filter (or filter only on an indexed non-person
  column), then select the rows whose person column matches: compare the name to
  LookupValue and the email to Email.
- When displaying person columns to the user, always show LookupValue (the
  display name). Never expose LookupId or raw email unless explicitly asked.

Formatting:
- Whenever you present structured or comparative data (lists of items with
  counts, amounts, dates, or any other attributes), always use a Markdown table.
- Use bullet lists only for short, non-comparative enumerations (e.g. a list of
  column names with no associated values).
- Never mix bullet lists and tables for the same dataset.
- Keep prose concise — lead with the table, follow with a brief note if needed.
"""


def _load_schema_doc() -> str:
    if _SCHEMA_DOC.exists():
        content = _SCHEMA_DOC.read_text()
        logger.info("Loaded SharePoint schema from %s", _SCHEMA_DOC)
        return "\n\n---\n\n" + content
    logger.warning(
        "sharepoint_schema.md not found — run scripts/fetch_schema.py to generate it"
    )
    return ""


def build_agent(service: SharePointService, settings: Settings) -> CompiledStateGraph:
    """Build a LangChain agent wired to the given SharePointService."""
    tools = make_tools(service)
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    )
    system_prompt = _BASE_PROMPT + _load_schema_doc()
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )


async def invoke_agent(
    agent: CompiledStateGraph,
    question: str,
    history: list[dict] | None = None,
) -> str:
    """Invoke the agent with optional conversation history and return the answer."""
    messages = (history or []) + [{"role": "user", "content": question}]
    result = await agent.ainvoke({"messages": messages})
    final = result["messages"][-1]
    if hasattr(final, "content"):
        return final.content
    return str(final)
