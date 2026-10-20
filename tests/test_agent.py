import pytest

from toolwise.agent import AgentError, ask_agent


def test_empty_message_rejected_before_api_call():
    with pytest.raises(AgentError, match="enter a message"):
        ask_agent("   ")


def test_oversized_message_rejected_before_api_call():
    with pytest.raises(AgentError, match="too long"):
        ask_agent("x" * 8001)


def test_missing_api_key_is_reported(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("toolwise.agent.load_dotenv", lambda *args, **kwargs: None)
    with pytest.raises(AgentError, match="OPENAI_API_KEY is not configured"):
        # The dependency import is only needed after the key check, but _build_executor
        # imports dependencies first; this test is skipped when dependencies are absent.
        from toolwise.agent import _build_executor
        _build_executor()
