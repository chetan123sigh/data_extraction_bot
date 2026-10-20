"""ToolWise AI agent using OpenAI models through LangChain tool calling."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .tools import calculate, get_stock_price, get_weather, web_search

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SYSTEM_PROMPT = """You are ToolWise AI, a helpful assistant that can use Python tools.
Use tools whenever a request needs weather, stock-price, arithmetic, or web-search data.
Never invent tool results. If a tool returns an error, explain it clearly and do not pretend
it succeeded. For stock data, state that the result may be delayed and is the latest available
close, not necessarily a live quote. For web-search answers, cite URLs returned by the tool.
If no tool is needed, answer normally. If the available data cannot establish a fact, say so.
"""


class AgentError(RuntimeError):
    """Safe errors for the interface to display."""


def _build_executor(model: str | None = None):
    """Create a LangChain OpenAI tool-calling agent and its executor."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        raise AgentError("OPENAI_API_KEY is not configured. Add your key to .env and restart the app.")

    try:
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.tools import tool
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise AgentError(
            "Agent dependencies are missing. Run: python -m pip install -r requirements.txt"
        ) from exc

    @tool("get_weather")
    def weather_tool(city: str) -> str:
        """Get current weather conditions for a city, such as Jaipur or Delhi."""
        return json.dumps(get_weather(city), ensure_ascii=False, default=str)

    @tool("get_stock_price")
    def stock_tool(symbol: str) -> str:
        """Get the latest available closing price for a stock ticker, e.g. AAPL or RELIANCE.NS."""
        return json.dumps(get_stock_price(symbol), ensure_ascii=False, default=str)

    @tool("calculate")
    def calculator_tool(expression: str) -> str:
        """Calculate an arithmetic expression using numbers, parentheses and arithmetic operators."""
        return json.dumps(calculate(expression), ensure_ascii=False, default=str)

    @tool("web_search")
    def search_tool(query: str) -> str:
        """Search the web for current or specific information and return source URLs."""
        return json.dumps(web_search(query), ensure_ascii=False, default=str)

    llm = ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        api_key=api_key,
        timeout=30,
        max_retries=2,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, [weather_tool, stock_tool, calculator_tool, search_tool], prompt)
    return AgentExecutor(
        agent=agent,
        tools=[weather_tool, stock_tool, calculator_tool, search_tool],
        max_iterations=5,
        max_execution_time=90,
        early_stopping_method="force",
        handle_parsing_errors="The tool request could not be parsed. Try a simpler request.",
        verbose=False,
        return_intermediate_steps=True,
    )


def ask_agent(
    message: str,
    history: list[dict[str, str]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a user request through a LangChain agent with OpenAI tool calling."""
    message = (message or "").strip()
    if not message:
        raise AgentError("Please enter a message.")
    if len(message) > 8000:
        raise AgentError("Message is too long (maximum 8,000 characters).")

    try:
        from langchain_core.messages import AIMessage, HumanMessage
        from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
    except ImportError as exc:
        raise AgentError("Dependencies are missing. Run: python -m pip install -r requirements.txt") from exc

    chat_history = []
    for item in (history or [])[-10:]:
        role, content = item.get("role"), item.get("content", "")
        if role == "user" and isinstance(content, str) and content.strip():
            chat_history.append(HumanMessage(content=content[:8000]))
        elif role == "assistant" and isinstance(content, str) and content.strip():
            chat_history.append(AIMessage(content=content[:8000]))

    try:
        result = _build_executor(model).invoke({"input": message, "chat_history": chat_history})
        calls = []
        for action, observation in result.get("intermediate_steps", []):
            try:
                parsed_observation = json.loads(observation) if isinstance(observation, str) else observation
            except (json.JSONDecodeError, TypeError):
                parsed_observation = {"result": str(observation)}
            calls.append({
                "tool": getattr(action, "tool", "unknown"),
                "arguments": getattr(action, "tool_input", {}),
                "result": parsed_observation,
            })
        return {
            "answer": str(result.get("output") or "I couldn't generate a response."),
            "tool_calls": calls,
            "model": model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        }
    except AgentError:
        raise
    except RateLimitError as exc:
        raise AgentError("OpenAI API rate limit or quota reached. Check API billing/limits, wait, and retry.") from exc
    except APITimeoutError as exc:
        raise AgentError("The AI request timed out. Please try again.") from exc
    except APIConnectionError as exc:
        raise AgentError("Could not connect to OpenAI. Check your internet connection.") from exc
    except APIStatusError as exc:
        if exc.status_code == 401:
            raise AgentError("OpenAI rejected the API key. Check OPENAI_API_KEY in .env.") from exc
        if exc.status_code == 429:
            raise AgentError("OpenAI API rate limit or quota reached. Check API billing/limits, wait, and retry.") from exc
        raise AgentError(f"OpenAI API returned HTTP {exc.status_code}. Check the model name and API status.") from exc
    except AgentError:
        raise
    except Exception as exc:
        # Do not expose raw provider errors or potentially sensitive request details to the UI.
        name = type(exc).__name__.lower()
        message_lower = str(exc).lower()
        if "rate" in name or "rate limit" in message_lower or "429" in message_lower:
            raise AgentError("The AI provider rate-limited this request. Wait briefly and retry.") from exc
        raise AgentError("The agent encountered an error. Check the API key, model, network, and terminal logs.") from exc
