"""Legal Worker — RAG on legal documents using Day 8 retrieval pipeline."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState
from Lab_Assignment.retrieval import retrieve


class LegalWorker:
    """Specialist worker for legal document retrieval and analysis."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, state: AgentState) -> dict:
        query = state["question"]
        results = retrieve(query, doc_type="legal", top_k=5)

        if not results:
            return {"legal_answer": "Không tìm thấy thông tin pháp lý liên quan.", "sources": []}

        context = "\n\n".join(
            f"[{r.get('source', r.get('metadata', {}).get('source', 'Unknown'))}]\n{r.get('content', '')[:500]}"
            for r in results
        )

        prompt = f"""You are a Vietnamese legal expert. Answer based ONLY on the context below.
Use citations in format [Tên luật, Điều X] for every factual claim.

Context:
{context}

Question: {query}

If the context lacks information, say 'Tôi không thể xác minh thông tin này từ nguồn hiện có'."""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {
            "legal_answer": response.content,
            "sources": [
                {
                    "source": r.get("source", r.get("metadata", {}).get("source", "?")),
                    "content": r.get("content", "")[:200],
                    "type": "legal",
                }
                for r in results
            ],
        }
