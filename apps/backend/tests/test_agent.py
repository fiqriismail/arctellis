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


def _azure_settings(**overrides):
    """A MagicMock Settings with Azure OpenAI fields set (api-key path)."""
    s = MagicMock()
    s.azure_openai_endpoint = "https://aoai.openai.azure.com"
    s.azure_openai_deployment = "gpt-4o-prod"
    s.azure_openai_api_version = "2024-10-21"
    s.azure_openai_api_key = "local-key"
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def test_build_llm_uses_api_key_when_provided():
    from langchain_openai import AzureChatOpenAI

    from app.agent import _build_llm

    llm = _build_llm(_azure_settings())

    assert isinstance(llm, AzureChatOpenAI)
    assert llm.deployment_name == "gpt-4o-prod"
    assert llm.azure_endpoint == "https://aoai.openai.azure.com"
    assert llm.openai_api_version == "2024-10-21"
    assert llm.openai_api_key.get_secret_value() == "local-key"
    # No managed-identity token provider when a key is supplied.
    assert llm.azure_ad_token_provider is None


def test_build_llm_uses_managed_identity_when_no_key():
    from app.agent import _build_llm

    def fake_provider():
        return "token"

    settings = _azure_settings(azure_openai_api_key="")
    with (
        patch("app.agent.DefaultAzureCredential") as mock_cred,
        patch(
            "app.agent.get_bearer_token_provider", return_value=fake_provider
        ) as mock_provider,
    ):
        llm = _build_llm(settings)

    # A credential is built and wired to a bearer-token provider for the
    # Cognitive Services scope — no static key is used.
    mock_cred.assert_called_once()
    assert (
        mock_provider.call_args[0][1] == "https://cognitiveservices.azure.com/.default"
    )
    assert llm.azure_ad_token_provider is fake_provider


def test_build_agent_uses_azure_openai_llm():
    from langchain_openai import AzureChatOpenAI

    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = _azure_settings()

    with patch("app.agent.create_agent") as mock_create:
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        assert mock_create.called
        kwargs = mock_create.call_args.kwargs
        llm = kwargs["model"]
        assert isinstance(llm, AzureChatOpenAI)
        assert llm.deployment_name == "gpt-4o-prod"


def test_build_agent_registers_all_tools():
    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = _azure_settings(site_timezone="Europe/London")

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
    mock_settings = _azure_settings()

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


# --- BE-09: clarification & out-of-scope prompt coverage ---


def test_system_prompt_prohibits_inventing_figures():
    from app.agent import _BASE_PROMPT

    assert "figures" in _BASE_PROMPT or "invent" in _BASE_PROMPT


def test_system_prompt_instructs_one_clarifying_question_at_a_time():
    from app.agent import _BASE_PROMPT

    assert "one clarifying question" in _BASE_PROMPT


# ---


def test_build_agent_passes_row_threshold_from_settings():
    from unittest.mock import patch

    from app.agent import build_agent

    mock_service = MagicMock()
    mock_settings = _azure_settings(
        site_timezone="Europe/London", list_row_threshold=500
    )

    with patch("app.agent.make_tools") as mock_make_tools, patch(
        "app.agent.create_agent"
    ) as mock_create:
        mock_make_tools.return_value = []
        mock_create.return_value = MagicMock()
        build_agent(mock_service, mock_settings)

        mock_make_tools.assert_called_once_with(
            mock_service,
            site_timezone="Europe/London",
            row_threshold=500,
        )


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
