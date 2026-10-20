import pytest

from toolwise.agent import AgentError, ask_agent


def test_empty_message_rejected_before_api_call():
    with pytest.raises(AgentError, match="enter a message"):
        ask_agent("   ")


def test_oversized_message_rejected_before_api_call():
    with pytest.raises(AgentError, match="too long"):
        ask_agent("x" * 8001)
