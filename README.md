# ToolWise AI — OpenAI + LangChain Agent with Tools

ToolWise AI is a Python chatbot that uses an OpenAI model through **LangChain Agents** and OpenAI-compatible tool/function calling to choose and execute specific Python functions. It includes a Streamlit chat interface and a terminal interface.

## Features

- **OpenAI + LangChain agent:** the model chooses a tool based on the user's intent; Python executes the selected function and returns its result to the agent.
- **Weather:** current conditions by city using Open-Meteo (no API key required).
- **Stock lookup:** latest available closing price using `yfinance`; this is not guaranteed to be a live quote.
- **Calculator:** arithmetic evaluated with a restricted Python AST allow-list, never `eval()`.
- **Web search:** DuckDuckGo search results with source URLs; availability can vary.
- **Streamlit UI and CLI:** use the browser interface or terminal.
- **Error handling:** empty/oversized input checks, tool argument validation, network timeouts, provider/rate-limit messages, and bounded agent iterations.
- **Tests:** unit tests run without making live OpenAI requests or relying on live data services.

## Requirements

- Python 3.10+ (Python 3.11 recommended).
- An OpenAI API key with API access and available billing/quota. ChatGPT Go/Plus subscriptions do not automatically include API credits.
- Internet access for OpenAI and external data tools.

## Setup on Windows 10/11

1. Extract the project and open the `multi_ai` folder in VS Code.
2. Open **Terminal → New Terminal** and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this in the same terminal and activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Create `.env` from the example:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Open `.env` and set your real OpenAI API key:

   ```dotenv
   OPENAI_API_KEY=your_real_openai_api_key
   OPENAI_MODEL=gpt-4.1-mini
   ```

   Do not add quotes unless your key requires them. Never share the key, paste it into source files, or commit `.env` to GitHub. `.gitignore` excludes `.env`.

## Run the Streamlit app

With the virtual environment activated and `.env` configured:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Run the CLI

```powershell
python cli.py
```

Type `exit` or `quit` to stop.

## Example prompts

- `What's the weather in Jaipur?`
- `Calculate 25% of 8000.`
- `Get the latest available closing price for AAPL.`
- `Get the latest available closing price for RELIANCE.NS.`
- `Search the web for the latest Python release.`
- `What's the weather in Delhi and calculate 15 * 24?`

## How tool calling works

1. The user sends a message.
2. The OpenAI model, orchestrated by a LangChain agent, decides whether a tool is needed and chooses its name and arguments.
3. LangChain validates and dispatches the tool call to a Python function.
4. The function returns structured data or a clear error result.
5. The agent uses that result to answer the user. The UI can show which tools were called and their results.

The model does not execute arbitrary Python. The calculator parses an expression into an AST and only allows numeric constants, parentheses, and a small allow-list of arithmetic operators.

## Run tests

```powershell
python -m pytest -v
```

Unit tests do not call the OpenAI API or external data services. A separate manual smoke test with a valid API key is needed to verify the complete live integration. API requests may incur charges.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | None | Secret used for OpenAI API requests |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | OpenAI model used by LangChain |

Weather uses Open-Meteo. Stock data comes from Yahoo Finance through `yfinance`. Web search uses DuckDuckGo through `ddgs`. Those providers may be unavailable or rate-limited.

## Project structure

```text
multi_ai/
├── app.py                 # Streamlit chat UI
├── cli.py                 # Terminal interface
├── requirements.txt        # OpenAI, LangChain, tools, and test dependencies
├── .env.example           # Environment variable template; no secrets
├── .gitignore             # Excludes .env and generated files
├── README.md
├── toolwise/
│   ├── __init__.py
│   ├── agent.py            # LangChain agent + OpenAI model/tool calling
│   └── tools.py            # Weather, stocks, calculator, web search
└── tests/
    ├── test_agent.py
    └── test_tools.py
```

## Limitations and responsible use

- Stock quotes may be delayed and are not financial advice.
- Weather is a current-conditions snapshot, not a guarantee of future weather.
- Search results are supplied by a third-party provider and should be checked against their original sources.
- OpenAI calls require internet access, a valid API key, and available account quota.
- Agent execution is capped to limit repeated tool calls.
- Never commit API keys or other secrets.

## Troubleshooting

- **`OPENAI_API_KEY is not configured`:** check that `.env` is in the same directory as `app.py` and contains your key, then restart the app.
- **HTTP 401:** verify the API key is correct and active.
- **HTTP 429 / quota:** check OpenAI API billing and rate limits, then wait and retry.
- **Model not found / unsupported model:** confirm the model name is available to your API account.
- **Weather unavailable:** check internet connectivity and retry later.
- **Stock unavailable:** verify the ticker (for example, Indian tickers often end in `.NS`) and retry later.
- **Search unavailable:** DuckDuckGo may throttle requests; retry later.

## GitHub safety

Before pushing, confirm `.env` is not staged or tracked. Commit `.env.example`, source code, tests, and documentation only. Do not push automatically; decide when you are ready.
