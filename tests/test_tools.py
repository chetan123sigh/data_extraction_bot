import pytest

from toolwise.tools import ToolError, calculate, run_tool


def test_calculate_basic_expression():
    assert calculate("(8000 * 25) / 100")["result"] == 2000


def test_calculate_power_and_parentheses():
    assert calculate("2 ** 3 + (10 - 4)")["result"] == 14


@pytest.mark.parametrize("expression", ["", "   ", "1 / 0", "__import__('os').system('echo bad')", "open('/etc/passwd').read()", "2 ** 1000"])
def test_calculate_rejects_invalid_or_dangerous_expressions(expression):
    with pytest.raises(ToolError):
        calculate(expression)


def test_calculate_rejects_long_input():
    with pytest.raises(ToolError):
        calculate("1" * 201)


def test_run_tool_handles_bad_tool_name():
    assert "error" in run_tool("not_a_tool", {})


def test_run_tool_handles_missing_argument():
    assert "error" in run_tool("get_weather", {})


def test_weather_rejects_empty_city_without_network():
    with pytest.raises(ToolError, match="city name"):
        from toolwise.tools import get_weather
        get_weather("  ")


def test_stock_rejects_empty_symbol_without_network():
    with pytest.raises(ToolError, match="ticker"):
        from toolwise.tools import get_stock_price
        get_stock_price("  ")


def test_web_search_rejects_empty_query_without_network():
    from toolwise.tools import web_search
    with pytest.raises(ToolError, match="search query"):
        web_search("  ")


def test_web_search_rejects_oversized_query_without_network():
    from toolwise.tools import web_search
    with pytest.raises(ToolError, match="too long"):
        web_search("x" * 301)
