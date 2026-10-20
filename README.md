# ToolWise AI 🤖

**ToolWise AI** is an AI-powered assistant that can use external tools to answer questions and perform tasks. Instead of relying only on an LLM's generated response, the agent can call tools for calculations, weather information, stock prices, and web searches.

Built with Python, Streamlit, and Ollama, this project can run locally without a paid LLM API key.

## ✨ Features

- **AI Agent:** Uses an LLM to decide when to call tools.
- **Calculator:** Evaluates supported mathematical expressions.
- **Weather:** Retrieves current weather information for a city.
- **Stock Lookup:** Retrieves available stock-price data using Yahoo Finance.
- **Web Search:** Searches the web for relevant information.
- **Local AI:** Runs supported language models using Ollama.
- **Streamlit UI:** Provides a browser-based interface.
- **CLI:** Includes a command-line entry point.
- **Tests:** Includes automated tests for project functionality.

## 🛠️ Tech Stack

- Python
- Ollama
- OpenAI-compatible Python client
- Streamlit
- Open-Meteo
- yfinance
- DuckDuckGo Search
- Pytest

## 📋 Prerequisites

Install the following before running the project:

1. **Python 3.10 or newer**
2. **Git**
3. **Ollama** — [Download Ollama](https://ollama.com/download)

A compatible local language model must be downloaded before starting the agent. Model performance depends on your computer's available RAM and hardware.

## 🚀 Installation and Setup

### 1. Download the project

Clone the repository using its GitHub URL:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with the actual GitHub username and repository name.

Alternatively, download the repository as a ZIP file from GitHub and extract it.

### 2. Create a virtual environment

**Windows — Git Bash:**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Windows — Command Prompt:**

```bat
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

Run this command from the project root directory:

```bash
python -m pip install -r requirements.txt
```

### 4. Install and start a local AI model

Open a terminal and download the default model:

```bash
ollama pull llama3.2:3b
```

Ollama usually runs in the background after installation. If it is not running, start its server in a separate terminal:

```bash
ollama serve
```

If you see an error saying port `11434` is already in use, Ollama may already be running. Do not start a second server.

Keep Ollama running while using ToolWise AI.

### 5. Configure environment variables

Create a file named `.env` in the project root, next to `app.py`.

Add:

```env
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.2:3b
```

**Important:** `ollama` is a placeholder value required by the OpenAI-compatible client in this local configuration. It is not a real API key.

You do not need a paid OpenAI API key for local Ollama inference.

Do not upload your `.env` file or any real API keys to GitHub.

### 6. Run the application

Make sure your virtual environment is activated and Ollama is running. From the project root, execute:

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

### 7. Run the command-line interface

To explore the CLI entry point, run:

```bash
python cli.py
```

Follow the prompts displayed by the application.

## 🧪 Testing

Run the automated test suite from the project root:

```bash
python -m pytest -v
```

Tests may cover tool functionality, agent behavior, input handling, and error cases.

## 💬 Example Prompts

Try these prompts in the application:

- `Calculate 125 * 48.`
- `Get the current weather in Jaipur.`
- `Find the latest available closing price of AAPL.`
- `Search the web for the latest Python release and provide its source URL.`

The agent should select the relevant tool when appropriate. Results from weather, financial data, and web searches depend on the external services and their available data.

## 📁 Project Structure

```text
multi_ai/
├── app.py                 # Streamlit application
├── cli.py                 # Command-line interface
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── LICENSE
├── tests/                 # Automated tests
└── toolwise/
    ├── agent.py           # AI agent and tool-calling loop
    └── tools.py           # Tool definitions and implementations
```

## 🔧 Troubleshooting

### Ollama connection error

- Ensure Ollama is installed and running.
- Check that the local API is reachable at `http://localhost:11434`.
- If necessary, start the server with `ollama serve`.

### Model not found

Download the configured model:

```bash
ollama pull llama3.2:3b
```

Make sure `OPENAI_MODEL` in `.env` matches the model name installed in Ollama.

### Python module not found

Activate the virtual environment and reinstall dependencies:

```bash
python -m pip install -r requirements.txt
```

### Streamlit command not found

With the virtual environment activated, try:

```bash
python -m streamlit run app.py
```

### Weather, stock, or web-search errors

These tools rely on external services. Check your internet connection and retry. Stock data availability and web-search results may vary.

## 💰 Cost

The default configuration uses a local Ollama model, so it does not require a paid LLM API key or incur per-request cloud inference charges. You still need a computer capable of running the model, and your electricity and internet usage may have their own costs.

Other services and models may have separate terms, limits, or charges if you change the configuration.

## 🔐 Privacy

With local Ollama inference, model prompts are processed by the local model server. However, weather, stock, and web-search tools send relevant queries to their respective external services. Avoid submitting passwords, private keys, or other sensitive information.

## 📌 Future Improvements

Potential enhancements include:

- More tools and integrations
- Improved agent memory
- Stronger input validation and error handling
- More automated tests
- Better logging and observability
- Additional local and cloud model options

