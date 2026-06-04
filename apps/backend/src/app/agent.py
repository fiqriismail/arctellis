from __future__ import annotations

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
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
- Always answer in plain English. Do not echo raw JSON or tool output directly to the user.
"""


def build_agent(service: SharePointService, settings: Settings) -> CompiledStateGraph:
    """Build a LangChain agent wired to the given SharePointService."""
    tools = make_tools(service)
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore[arg-type]
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
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
