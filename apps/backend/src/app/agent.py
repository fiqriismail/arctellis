from __future__ import annotations

import logging
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain.agents import create_agent
from langchain_openai import AzureChatOpenAI
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
- Use only the provided tools to fetch data — never fabricate column names,
  values, or figures.
- All arithmetic is performed by the tools; never compute numbers yourself.
- If a question is ambiguous or references a column that does not exist, ask
  one clarifying question rather than guessing. Do not ask multiple questions
  at once.
- If a question is unrelated to the SharePoint list, politely decline to answer.
  Do not attempt a partial or speculative response.
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
- Boolean columns (type 'boolean'): filter with 1 (true) or 0 (false) in OData,
  e.g. fields/InfoSecReviewRequired eq 1. The tools rewrite eq true/false
  automatically — never hand-filter booleans in memory unless OData is unsuitable.
- Lookup columns (type 'lookup', e.g. Category) are returned as objects with:
    - "LookupValue": the display name from the linked taxonomy/list item
  Category points at the category taxonomy list — use LookupValue when
  filtering in memory or presenting results. OData filters on lookup columns
  use the hidden id field (e.g. fields/CategoryLookupId eq 109), not the
  display name.
- Date/time columns: for ANY question about a date or day (e.g. "items created
  on 25 May 2026", "modified last week"), use the filter_by_date tool with the
  column's internal name and YYYY-MM-DD dates. It interprets dates in the site's
  local timezone and converts to the correct UTC range — do NOT hand-build a
  datetime odata_filter, as Graph stores dates in UTC and naive filters miss
  rows near midnight.

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


# Entra ID scope for Azure OpenAI (Cognitive Services) data-plane access.
_AOAI_SCOPE = "https://cognitiveservices.azure.com/.default"


def _build_llm(settings: Settings) -> AzureChatOpenAI:
    """Construct the Azure OpenAI chat model.

    Authenticates with the container's managed identity by default (no secret in
    config). A static API key is used only when ``azure_openai_api_key`` is set,
    which is intended for local development.
    """
    common = {
        "azure_endpoint": settings.azure_openai_endpoint,
        "azure_deployment": settings.azure_openai_deployment,
        "api_version": settings.azure_openai_api_version,
    }
    if settings.azure_openai_api_key:
        return AzureChatOpenAI(api_key=settings.azure_openai_api_key, **common)

    token_provider = get_bearer_token_provider(DefaultAzureCredential(), _AOAI_SCOPE)
    return AzureChatOpenAI(azure_ad_token_provider=token_provider, **common)


def build_agent(service: SharePointService, settings: Settings) -> CompiledStateGraph:
    """Build a LangChain agent wired to the given SharePointService."""
    tools = make_tools(
        service,
        site_timezone=settings.site_timezone,
        row_threshold=settings.list_row_threshold,
    )
    llm = _build_llm(settings)
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
