"""Streamlit UI for ToolWise AI."""
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from toolwise.agent import AgentError, ask_agent

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(page_title="ToolWise AI", page_icon="🧰", layout="centered")
st.title("🧰 ToolWise AI")
st.caption("An OpenAI-powered LangChain agent that chooses and runs Python tools for weather, stocks, calculations, and web search.")

with st.sidebar:
    st.header("Available tools")
    st.markdown("- 🌦️ **Weather** — current conditions by city\n- 📈 **Stock lookup** — latest available closing price\n- 🧮 **Calculator** — safe arithmetic\n- 🔎 **Web search** — search results with source links")
    st.divider()
    st.markdown("**Try asking**")
    st.markdown('- "What is the weather in Jaipur?"\n- "Calculate 25% of 8000"\n- "Get the latest available price for AAPL"\n- "Search for the latest Python release"')
    st.caption("Weather is provided by Open-Meteo. Stock data may be delayed.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("tool_calls"):
            with st.expander(f"Tools used ({len(message['tool_calls'])})"):
                for call in message["tool_calls"]:
                    st.markdown(f"**{call['tool']}**")
                    st.json({"arguments": call["arguments"], "result": call["result"]})

prompt = st.chat_input("Ask ToolWise AI to do something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking and selecting tools..."):
            try:
                result = ask_agent(prompt, history=st.session_state.agent_history)
                answer = result["answer"]
                st.markdown(answer)
                if result["tool_calls"]:
                    with st.expander(f"Tools used ({len(result['tool_calls'])})"):
                        for call in result["tool_calls"]:
                            st.markdown(f"**{call['tool']}**")
                            st.json({"arguments": call["arguments"], "result": call["result"]})
                st.session_state.messages.append({"role": "assistant", "content": answer, "tool_calls": result["tool_calls"]})
                st.session_state.agent_history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}])
                st.session_state.agent_history = st.session_state.agent_history[-10:]
            except AgentError as exc:
                st.error(str(exc))
                st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {exc}"})
