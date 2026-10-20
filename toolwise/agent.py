
"""Ollama-compatible tool-calling agent for ToolWise AI."""
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from .tools import TOOL_DEFINITIONS, run_tool

SYSTEM_PROMPT = """You are ToolWise AI, a helpful assistant with tools.
Use tools for weather, stock prices, arithmetic, and web search when needed.
Never invent tool results. Explain tool errors. Stock prices may be delayed.
Cite URLs returned by web search. If no tool is needed, answer normally."""


class AgentError(RuntimeError):
    """Safe errors for the interface to display."""


def _client():
    return OpenAI(
        base_url="http://localhost:11434/v1",
        api_key=os.getenv("OPENAI_API_KEY", "ollama"),
        timeout=120,
        max_retries=2,
    )


def ask_agent(
    message: str,
    history: list[dict[str, str]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    message = (message or "").strip()
    if not message:
        raise AgentError("Please enter a message.")
    if len(message) > 8000:
        raise AgentError("Message is too long (maximum 8,000 characters).")

    client = _client()
    chosen_model = model or os.getenv("OPENAI_MODEL", "llama3.2:3b")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in (history or [])[-10:]:
        role, content = item.get("role"), item.get("content", "")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content[:8000]})
    messages.append({"role": "user", "content": message})

    tool_calls = []

    try:
        for _ in range(5):
            response = client.chat.completions.create(
                model=chosen_model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            choice = response.choices[0]
            assistant_message = choice.message
            messages.append(assistant_message.model_dump(exclude_none=True))

            if not assistant_message.tool_calls:
                return {
                    "answer": assistant_message.content or "I couldn't generate a response.",
                    "tool_calls": tool_calls,
                    "model": chosen_model,
                }

            for call in assistant_message.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                    if not isinstance(args, dict):
                        raise ValueError("Tool arguments must be an object.")
                    result = run_tool(call.function.name, args)
                except (json.JSONDecodeError, ValueError):
                    args = {}
                    result = {"error": "The AI supplied invalid tool arguments."}

                tool_calls.append({
                    "tool": call.function.name,
                    "arguments": args,
                    "result": result,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        raise AgentError("The agent reached its tool-call limit. Please be more specific.")
    except AgentError:
        raise
    except Exception as exc:
        raise AgentError(
            f"AI request failed. Ensure Ollama is running and model '{chosen_model}' is installed. "
            "Check the terminal for details."
        ) from exc
