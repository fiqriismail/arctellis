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
