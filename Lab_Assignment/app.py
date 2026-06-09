"""Lab Assignment — RAG Chatbot with Supervisor-Workers Pattern."""

import asyncio
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Lab_Assignment.agents.supervisor import SupervisorAgent

st.set_page_config(page_title="Supervisor-Workers RAG", page_icon="🤖", layout="wide")
st.title("🤖 Supervisor-Workers RAG — Legal Multi-Agent")
st.markdown("""
**Supervisor** → phân tích → **Legal Worker** + **News Worker** (parallel) → **Synthesis Worker**
""")

@st.cache_resource
def load_agent():
    return SupervisorAgent()

agent = load_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.sources = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Hỏi về luật ma túy hoặc nghệ sĩ liên quan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Supervisor đang phân tích → Workers đang xử lý..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(agent.ask(prompt))
            loop.close()

        st.markdown(result["answer"])
        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

        if result.get("sources"):
            with st.expander(f"📚 Nguồn ({len(result['sources'])})"):
                for s in result["sources"]:
                    st.caption(f"**{s['source']}** ({s.get('type', '?')})")
                    st.code(s.get("content", "")[:200] + "...")
