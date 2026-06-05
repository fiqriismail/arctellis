from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# --- base prompt content ---


def test_system_prompt_instructs_get_schema_first():
    from app.agent import _BASE_PROMPT

    assert "get_schema" in _BASE_PROMPT


def test_system_prompt_prohibits_fabrication():
    from app.agent import _BASE_PROMPT

    assert "fabricat" in _BASE_PROMPT


def test_system_prompt_requests_clarification():
    from app.agent import _BASE_PROMPT

    assert "clarif" in _BASE_PROMPT


def test_system_prompt_handles_unrelated_questions():
    from app.agent import _BASE_PROMPT

    assert "decline" in _BASE_PROMPT or "unrelated" in _BASE_PROMPT


# --- build_agent ---


def test_build_agent_passes_correct_model_string():
    from langchain_openai import ChatOpenAI

    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"
    mock_settings.openai_api_key = "sk-test"

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        assert mock_create.called
        kwargs = mock_create.call_args.kwargs
        llm = kwargs["model"]
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o"
        assert llm.openai_api_key.get_secret_value() == "sk-test"


def test_build_agent_registers_all_tools():
    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"
    mock_settings.openai_api_key = "sk-test"
    mock_settings.site_timezone = "Europe/London"

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
            "filter_by_date",
        }


def test_build_agent_passes_system_prompt():
    from app.agent import _BASE_PROMPT, build_agent

    mock_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.openai_model = "gpt-4o"
    mock_settings.openai_api_key = "sk-test"

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        kwargs = mock_create.call_args.kwargs
        # The full prompt is the base prompt plus any generated schema doc.
        assert kwargs["system_prompt"].startswith(_BASE_PROMPT)


# --- invoke_agent ---


@pytest.mark.asyncio
async def test_invoke_agent_returns_content_from_last_message():
    from langchain_core.messages import AIMessage

    from app.agent import invoke_agent

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="The total budget is 5000.")]}
    )

    result = await invoke_agent(mock_agent, "What is the total budget?")
    assert result == "The total budget is 5000."


@pytest.mark.asyncio
async def test_invoke_agent_no_history_sends_one_message():
    from langchain_core.messages import AIMessage

    from app.agent import invoke_agent

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
    from langchain_core.messages import AIMessage

    from app.agent import invoke_agent

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(return_value={"messages": [AIMessage(content="ok")]})

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
    from langchain_core.messages import AIMessage

    from app.agent import invoke_agent

    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="answer")]}
    )

    await invoke_agent(mock_agent, "question", history=None)

    sent = mock_agent.ainvoke.call_args[0][0]["messages"]
    assert len(sent) == 1
