# BE-05 LangChain Agent + OpenAI Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire a LangChain agent to OpenAI and the BE-04 list data tools so the model can interpret questions, call the right tools, and phrase a final answer — without computing any figures itself.

**Architecture:** `agent.py` exposes two functions: `build_agent(service, settings)` which calls `create_agent()` from `langchain.agents` with the model string `"openai:{settings.openai_model}"`, the six tools from `make_tools(service)`, and a `SYSTEM_PROMPT`; and `invoke_agent(agent, question, history)` which calls `agent.ainvoke()` and extracts the final message content. Tests patch `create_agent` so no OpenAI key is needed for unit tests. A `verify_agent.py` script exercises the real agent end-to-end.

**Tech Stack:** Python 3.13 · `langchain>=1.0` (`create_agent`) · `langchain-core>=1.0` (`AIMessage`) · `langchain-openai>=1.0` · `langgraph` · pytest · pytest-asyncio · uv

**Story:** BE-05
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/config.py` — `Settings` with `openai_model: str = "gpt-4o"` and `openai_api_key`
- `src/app/services/sharepoint.py` — `SharePointService`, `create_sharepoint_service()`
- `src/app/services/graph_auth.py` — `GraphAuthService`
- `src/app/tools/list_tools.py` — `make_tools(service) -> list` returning 6 `@tool` closures
- Installed: `langchain==1.3.4`, `langchain-core==1.4.0`, `langchain-openai==1.2.2`
- `create_agent(model, tools, *, system_prompt, ...)` — `langchain.agents`; returns `CompiledStateGraph`
- `init_chat_model(model_string)` — `langchain.chat_models`; returns `BaseChatModel`

---

## File Map

```
apps/backend/
├── src/app/
│   └── agent.py                ← SYSTEM_PROMPT + build_agent() + invoke_agent()
├── tests/
│   └── test_agent.py           ← unit tests (create_agent patched, no OpenAI calls)
└── scripts/
    └── verify_agent.py         ← integration harness (requires .env)
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-05-langchain-agent
```

Expected: `Switched to a new branch 'feature/BE-05-langchain-agent'`

---

## Task 2: `SYSTEM_PROMPT` + `build_agent()` (TDD)

**Files:**
- Create: `apps/backend/src/app/agent.py`
- Create: `apps/backend/tests/test_agent.py`

- [ ] **Step 2.1: Write failing tests**

Create `apps/backend/tests/test_agent.py`:

```python
from unittest.mock import MagicMock, patch


# --- SYSTEM_PROMPT content ---

def test_system_prompt_instructs_get_schema_first():
    from app.agent import SYSTEM_PROMPT

    assert "get_schema" in SYSTEM_PROMPT


def test_system_prompt_prohibits_fabrication():
    from app.agent import SYSTEM_PROMPT

    assert "fabricat" in SYSTEM_PROMPT


def test_system_prompt_requests_clarification():
    from app.agent import SYSTEM_PROMPT

    assert "clarif" in SYSTEM_PROMPT


def test_system_prompt_handles_unrelated_questions():
    from app.agent import SYSTEM_PROMPT

    assert "decline" in SYSTEM_PROMPT or "unrelated" in SYSTEM_PROMPT


# --- build_agent ---

def test_build_agent_passes_correct_model_string():
    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        assert mock_create.called
        kwargs = mock_create.call_args.kwargs
        assert kwargs["model"] == "openai:gpt-4o"


def test_build_agent_registers_all_six_tools():
    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        kwargs = mock_create.call_args.kwargs
        tool_names = {t.name for t in kwargs["tools"]}
        assert tool_names == {
            "get_schema",
            "filter_rows",
            "count_rows",
            "sum_column",
            "average_column",
            "group_and_aggregate",
        }


def test_build_agent_passes_system_prompt():
    from app.agent import build_agent, SYSTEM_PROMPT

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        kwargs = mock_create.call_args.kwargs
        assert kwargs["system_prompt"] == SYSTEM_PROMPT
```

- [ ] **Step 2.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_agent.py::test_system_prompt_instructs_get_schema_first -v
```

Expected: `ModuleNotFoundError: No module named 'app.agent'`

- [ ] **Step 2.3: Implement `agent.py`**

Create `apps/backend/src/app/agent.py`:

```python
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
```

- [ ] **Step 2.4: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_agent.py -v
```

Expected: 7 passed.

- [ ] **Step 2.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/agent.py apps/backend/tests/test_agent.py
git commit -m "feat(backend): add build_agent and SYSTEM_PROMPT (BE-05)"
```

---

## Task 3: `invoke_agent()` (TDD)

**Files:**
- Modify: `apps/backend/src/app/agent.py`
- Modify: `apps/backend/tests/test_agent.py`

- [ ] **Step 3.1: Append failing tests**

Append to the end of `apps/backend/tests/test_agent.py`:

```python
import pytest
from unittest.mock import AsyncMock


# --- invoke_agent ---

@pytest.mark.asyncio
async def test_invoke_agent_returns_content_from_last_message():
    from app.agent import invoke_agent
    from langchain_core.messages import AIMessage

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="The total budget is 5000.")]}
    )

    result = await invoke_agent(mock_agent, "What is the total budget?")
    assert result == "The total budget is 5000."


@pytest.mark.asyncio
async def test_invoke_agent_no_history_sends_one_message():
    from app.agent import invoke_agent
    from langchain_core.messages import AIMessage

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="answer")]}
    )

    await invoke_agent(mock_agent, "How many items?")

    sent = mock_agent.ainvoke.call_args[0][0]["messages"]
    assert len(sent) == 1
    assert sent[0]["content"] == "How many items?"
    assert sent[0]["role"] == "user"


@pytest.mark.asyncio
async def test_invoke_agent_prepends_history():
    from app.agent import invoke_agent
    from langchain_core.messages import AIMessage

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="ok")]}
    )

    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    await invoke_agent(mock_agent, "follow-up question", history=history)

    sent = mock_agent.ainvoke.call_args[0][0]["messages"]
    assert len(sent) == 3
    assert sent[0]["content"] == "hi"
    assert sent[1]["content"] == "hello"
    assert sent[2]["content"] == "follow-up question"


@pytest.mark.asyncio
async def test_invoke_agent_none_history_treated_as_empty():
    from app.agent import invoke_agent
    from langchain_core.messages import AIMessage

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="answer")]}
    )

    await invoke_agent(mock_agent, "question", history=None)

    sent = mock_agent.ainvoke.call_args[0][0]["messages"]
    assert len(sent) == 1
```

- [ ] **Step 3.2: Run — verify new tests FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_agent.py::test_invoke_agent_returns_content_from_last_message -v
```

Expected: `ImportError: cannot import name 'invoke_agent'`

- [ ] **Step 3.3: Add `invoke_agent` to `agent.py`**

Append to `apps/backend/src/app/agent.py`:

```python

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
```

- [ ] **Step 3.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_agent.py -v
```

Expected: 11 passed.

- [ ] **Step 3.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/agent.py apps/backend/tests/test_agent.py
git commit -m "feat(backend): add invoke_agent helper (BE-05)"
```

---

## Task 4: Integration verification script

**Files:**
- Create: `apps/backend/scripts/verify_agent.py`

This script calls the real OpenAI API and real SharePoint list. It requires a populated `.env`.

- [ ] **Step 4.1: Create the script**

Create `apps/backend/scripts/verify_agent.py`:

```python
"""
Verification script for BE-05 — LangChain Agent.

Run from apps/backend/:
    uv run python scripts/verify_agent.py

Requires a populated .env (OPENAI_API_KEY, OPENAI_MODEL, Azure + SharePoint creds).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service
from app.agent import build_agent, invoke_agent


async def verify() -> None:
    settings = Settings()
    print("=== BE-05 LangChain Agent Verification ===\n")
    print(f"Model: openai:{settings.openai_model}\n")

    auth = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    print("1. Connecting to SharePoint...")
    service = await create_sharepoint_service(auth_service=auth, settings=settings)
    print("   OK\n")

    print("2. Building agent...")
    agent = build_agent(service, settings)
    print("   OK\n")

    print("3. Question: What columns are available in this list?")
    answer = await invoke_agent(agent, "What columns are available in this list?")
    print(f"   Answer: {answer[:300]}\n")

    print("4. Question: How many items are in the list?")
    answer = await invoke_agent(agent, "How many items are in the list?")
    print(f"   Answer: {answer}\n")

    print("5. Question: What is the weather today? (should decline)")
    answer = await invoke_agent(agent, "What is the weather today?")
    print(f"   Answer: {answer}\n")

    print("=== Verification complete ===")


if __name__ == "__main__":
    asyncio.run(verify())
```

- [ ] **Step 4.2: Run the script**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run python scripts/verify_agent.py
```

Expected:
- Question 3: agent calls `get_schema` and lists column names
- Question 4: agent calls `count_rows` and returns a number
- Question 5: agent politely declines (confirms FR-11)

If any question fails (e.g. wrong tool called, fabricated answer), diagnose and fix `SYSTEM_PROMPT` in `agent.py` before committing.

- [ ] **Step 4.3: Commit the script**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/scripts/verify_agent.py
git commit -m "feat(backend): add agent verification script (BE-05)"
```

---

## Task 5: Ruff lint + push

- [ ] **Step 5.1: Run ruff**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
```

Fix any issues:

```bash
uv run ruff format src/ tests/ scripts/
uv run ruff check --fix src/ tests/ scripts/
```

- [ ] **Step 5.2: Commit fixes if any**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/ apps/backend/scripts/
git diff --staged --quiet || git commit -m "style(backend): ruff formatting (BE-05)"
```

- [ ] **Step 5.3: Final test run**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

All tests must pass.

- [ ] **Step 5.4: Push**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-05-langchain-agent
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Agent created with `create_agent(model=..., tools=[...], system_prompt=...)` | Task 2 |
| `init_chat_model(f"openai:{settings.openai_model}")` — model from config | Task 2: `model=f"openai:{settings.openai_model}"` passed directly to `create_agent` (which calls `init_chat_model` internally) |
| Tools from BE-04 registered | Task 2: `make_tools(service)` passed as `tools=` |
| Model decides which tools to call (FR-7) | Task 4: verified by running script and observing tool calls |
| Ambiguous / unknown column → clarifying question (FR-10) | Task 2: SYSTEM_PROMPT contains "clarif" instruction; Task 4: verified via script |
| Unrelated questions → polite decline (FR-11, NFR-6) | Task 2: SYSTEM_PROMPT contains "decline/unrelated" instruction; Task 4: question 5 verifies |
| End-to-end tool calling demonstrated (Phase 2 exit) | Task 4: questions 3 and 4 exercise `get_schema` and `count_rows` |

**Placeholder scan:** None found.

**Type consistency:**
- `build_agent(service: SharePointService, settings: Settings) -> CompiledStateGraph` — consistent across Task 2 impl, tests, and verify script.
- `invoke_agent(agent: CompiledStateGraph, question: str, history: list[dict] | None = None) -> str` — consistent across Task 3 impl, tests, and verify script.
- `SYSTEM_PROMPT` — string constant imported in both tests and verify script.
