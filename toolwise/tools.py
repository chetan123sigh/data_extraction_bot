"""Tools exposed to the ToolWise AI agent.

Weather uses the free Open-Meteo APIs (no key required). Stock data uses yfinance.
Web search uses the optional ddgs package. Calculator evaluates a restricted AST,
never Python eval(), so user expressions cannot execute arbitrary code.
"""
from __future__ import annotations

import ast
import math
import operator
import os
from typing import Any

import requests

TIMEOUT = 12


class ToolError(Exception):
    """A safe, user-presentable tool failure."""


def calculate(expression: str) -> dict[str, Any]:
    """Evaluate basic arithmetic with a strict AST allow-list."""
    if not isinstance(expression, str) or not expression.strip():
        raise ToolError("Please provide a non-empty arithmetic expression.")
    if len(expression) > 200:
        raise ToolError("Expression is too long (maximum 200 characters).")

    binary_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def visit(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 10**12:
                raise ToolError("Number is outside the supported range.")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ToolError("Exponent is too large.")
            result = binary_ops[type(node.op)](left, right)
            if isinstance(result, complex) or not math.isfinite(float(result)):
                raise ToolError("Result is not a finite real number.")
            if abs(result) > 10**100:
                raise ToolError("Result is outside the supported range.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            return unary_ops[type(node.op)](visit(node.operand))
        raise ToolError("Only numbers, parentheses, +, -, *, /, //, %, and ** are allowed.")

    try:
        result = visit(ast.parse(expression, mode="eval"))
    except ToolError:
        raise
    except ZeroDivisionError as exc:
        raise ToolError("Cannot divide by zero.") from exc
    except (SyntaxError, ValueError, OverflowError, TypeError) as exc:
        raise ToolError("Invalid or unsupported arithmetic expression.") from exc
    return {"expression": expression, "result": result}


def get_weather(city: str) -> dict[str, Any]:
    """Fetch current weather for a city using Open-Meteo."""
    city = (city or "").strip()
    if not city:
        raise ToolError("Please provide a city name.")
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=TIMEOUT,
        )
        geo.raise_for_status()
        results = geo.json().get("results", [])
        if not results:
            raise ToolError(f"I couldn't find a location named '{city}'. Check the spelling.")
        place = results[0]
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"], "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
                "timezone": "auto",
            }, timeout=TIMEOUT,
        )
        response.raise_for_status()
        current = response.json().get("current")
        if not current:
            raise ToolError("The weather provider returned no current conditions.")
        return {
            "location": ", ".join(filter(None, [place.get("name"), place.get("admin1"), place.get("country")])),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "precipitation_mm": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "observed_at": current.get("time"),
            "source": "Open-Meteo",
        }
    except ToolError:
        raise
    except requests.Timeout as exc:
        raise ToolError("Weather request timed out. Please try again.") from exc
    except requests.RequestException as exc:
        raise ToolError("Weather service is temporarily unavailable. Please try again later.") from exc
    except (ValueError, KeyError) as exc:
        raise ToolError("Weather service returned an unexpected response.") from exc


def get_stock_price(symbol: str) -> dict[str, Any]:
    """Fetch the latest available quote/history using yfinance."""
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ToolError("Please provide a stock ticker, for example AAPL or RELIANCE.NS.")
    if len(symbol) > 20 or not all(c.isalnum() or c in ".-^=" for c in symbol):
        raise ToolError("Invalid ticker format. Use a stock symbol such as AAPL or RELIANCE.NS.")
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", auto_adjust=False)
        if hist.empty or "Close" not in hist:
            raise ToolError(f"No recent price data found for '{symbol}'. Check the ticker symbol.")
        row = hist.dropna(subset=["Close"]).iloc[-1]
        info: dict[str, Any] = {}
        try:
            info = ticker.get_info()
        except Exception:
            pass
        return {
            "symbol": symbol,
            "company": info.get("shortName") or info.get("longName") or symbol,
            "latest_available_close": round(float(row["Close"]), 4),
            "currency": info.get("currency", "provider default"),
            "date": str(hist.dropna(subset=["Close"]).index[-1].date()),
            "source": "Yahoo Finance via yfinance",
            "note": "This is the latest available closing price, not necessarily a live quote. Data may be delayed.",
        }
    except ToolError:
        raise
    except ImportError as exc:
        raise ToolError("Stock lookup dependency is missing. Install requirements.txt and try again.") from exc
    except Exception as exc:
        message = str(exc).lower()
        if "rate limit" in message or "too many requests" in message:
            raise ToolError("The stock provider rate-limited this request. Wait briefly and try again.") from exc
        raise ToolError("Stock data is temporarily unavailable. Check the ticker or try again later.") from exc


def web_search(query: str) -> dict[str, Any]:
    """Search the web with DuckDuckGo, if the optional package is installed."""
    query = (query or "").strip()
    if not query:
        raise ToolError("Please provide a search query.")
    if len(query) > 300:
        raise ToolError("Search query is too long (maximum 300 characters).")
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return {"query": query, "results": [], "message": "No search results found."}
        return {
            "query": query,
            "results": [{"title": r.get("title", "Untitled"), "url": r.get("href", ""), "snippet": r.get("body", "")} for r in results],
            "source": "DuckDuckGo search",
        }
    except ImportError as exc:
        raise ToolError("Web search dependency is missing. Install requirements.txt and try again.") from exc
    except Exception as exc:
        if "rate" in str(exc).lower() or "429" in str(exc):
            raise ToolError("Web search was rate-limited. Please wait and try again.") from exc
        raise ToolError("Web search is temporarily unavailable. Please try again later.") from exc


TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
    "calculate": calculate,
    "web_search": web_search,
}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Use for weather or temperature questions.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name, e.g. Jaipur"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the latest available closing price for a stock ticker. Examples: AAPL, MSFT, RELIANCE.NS.",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string", "description": "Stock ticker symbol"}},
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate arithmetic accurately. Supports +, -, *, /, //, %, ** and parentheses.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Arithmetic expression, e.g. (8000 * 25) / 100"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current or specific information that needs external sources.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Concise web search query"}},
                "required": ["query"],
            },
        },
    },
]



def run_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run a named tool with consistent, safe error output."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except ToolError as exc:
        return {"error": str(exc)}
    except TypeError:
        return {"error": f"Invalid arguments supplied to {name}."}
    except Exception:
        # Keep internal tracebacks and secrets out of the user-facing response.
        return {"error": f"The {name} tool failed unexpectedly. Please try again."}
