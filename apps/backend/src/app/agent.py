from __future__ import annotations

from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings
from app.services.sharepoint import SharePointService
from app.tools.list_tools import make_tools

SYSTEM_PROMPT = """\
You are an assistant that answers questions about a SharePoint list.

Guidelines:
- Always call get_schema first to understand the available columns before querying.
- Use only the provided tools to fetch data — never fabricate column names, values, or figures.
- All arithmetic is performed by the tools; never compute numbers yourself.
- If a question is ambiguous or references a column that does not exist, ask a clarifying question rather than guessing.
- If a question is unrelated to the SharePoint list, politely decline to answer.
"""


def build_agent(service: SharePointService, settings: Settings) -> CompiledStateGraph:
    """Build a LangChain agent wired to the given SharePointService."""
    tools = make_tools(service)
    return create_agent(
        model=f"openai:{settings.openai_model}",
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
