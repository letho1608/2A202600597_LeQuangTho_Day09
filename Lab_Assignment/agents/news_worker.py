"""News Worker — RAG on news articles using Day 8 retrieval pipeline."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState
from Lab_Assignment.retrieval import retrieve


class NewsWorker:
    """Specialist worker for news article retrieval and analysis."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, state: AgentState) -> dict:
        query = state["question"]
        results = retrieve(query, doc_type="news", top_k=5)

        if not results:
            return {"news_answer": "Không tìm thấy tin tức liên quan.", "sources": []}

        context = "\n\n".join(
            f"[{r.get('source', r.get('metadata', {}).get('source', 'Unknown'))}]\n{r.get('content', '')[:500]}"
            for r in results
        )

        prompt = f"""You are a news analyst. Answer based ONLY on the context below.
Use citations in format [Nguồn, Năm] for every factual claim.

Context:
{context}

Question: {query}

If the context lacks information, say so clearly."""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {
            "news_answer": response.content,
            "sources": [
                {
                    "source": r.get("source", r.get("metadata", {}).get("source", "?")),
                    "content": r.get("content", "")[:200],
                    "type": "news",
                }
                for r in results
            ],
        }
