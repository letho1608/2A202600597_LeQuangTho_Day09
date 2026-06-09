"""News Worker — RAG on news articles about celebrities and drugs."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState

NEWS_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "standardized" / "news"


class NewsWorker:
    """Specialist worker for news article retrieval and analysis."""

    def __init__(self):
        self.llm = get_llm()
        self.documents = self._load_documents()

    def _load_documents(self) -> list[dict]:
        if NEWS_DATA_DIR.exists():
            docs = []
            for f in sorted(NEWS_DATA_DIR.glob("*.md")):
                docs.append({
                    "source": f.stem,
                    "content": f.read_text(encoding="utf-8"),
                    "type": "news",
                })
            if docs:
                return docs
        return self._sample_docs()

    def _sample_docs(self) -> list[dict]:
        return [
            {
                "source": "VnExpress 2024",
                "content": (
                    "Ca sĩ X bị tạm giữ vì tàng trữ ma túy tại nhà riêng ở TP.HCM. "
                    "Công an thu giữ 100g ma túy tổng hợp. Người vi phạm có thể đối mặt "
                    "với mức án 2-7 năm tù theo Điều 249 Bộ luật Hình sự."
                ),
                "type": "news",
            },
            {
                "source": "Tuổi Trẻ 2024",
                "content": (
                    "Diễn viên Y bị khởi tố về hành vi tổ chức sử dụng trái phép chất ma túy. "
                    "Vụ việc xảy ra tại một chung cư cao cấp ở Hà Nội. "
                    "Theo Điều 255, tội tổ chức sử dụng ma túy có khung hình phạt từ 7-15 năm tù."
                ),
                "type": "news",
            },
            {
                "source": "Thanh Niên 2025",
                "content": (
                    "Người mẫu Z dương tính với ma túy trong đợt kiểm tra đột xuất. "
                    "Sự việc gây chấn động dư luận và ảnh hưởng nghiêm trọng đến sự nghiệp. "
                    "Sử dụng trái phép chất ma túy bị xử phạt hành chính hoặc giáo dục tại địa phương."
                ),
                "type": "news",
            },
        ]

    def _search(self, query: str, top_k: int = 3) -> list[dict]:
        q = query.lower()
        scored = []
        for doc in self.documents:
            score = sum(1 for kw in q.split() if kw in doc["content"].lower())
            if score > 0:
                scored.append({**doc, "score": score / max(len(q.split()), 1)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def run(self, state: AgentState) -> dict:
        query = state["question"]
        results = self._search(query)

        if not results:
            return {
                "news_answer": "Không tìm thấy tin tức liên quan.",
                "sources": [],
            }

        context = "\n\n".join(f"[{r['source']}]\n{r['content']}" for r in results)

        prompt = f"""You are a news analyst. Answer based ONLY on the context below.
Use citations in format [Nguồn, Năm] for every factual claim.

Context:
{context}

Question: {query}

If the context lacks information, say so clearly."""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {
            "news_answer": response.content,
            "sources": [{"source": r["source"], "content": r["content"][:200], "type": r["type"]} for r in results],
        }
