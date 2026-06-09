"""Legal Worker — RAG on legal documents using Day 8 pipeline."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState

LEGAL_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "standardized" / "legal"


class LegalWorker:
    """Specialist worker for legal document retrieval and analysis."""

    def __init__(self):
        self.llm = get_llm()
        self.documents = self._load_documents()

    def _load_documents(self) -> list[dict]:
        if LEGAL_DATA_DIR.exists():
            docs = []
            for f in sorted(LEGAL_DATA_DIR.glob("*.md")):
                docs.append({
                    "source": f.stem,
                    "content": f.read_text(encoding="utf-8"),
                    "type": "legal",
                })
            if docs:
                return docs
        return self._sample_docs()

    def _sample_docs(self) -> list[dict]:
        return [
            {
                "source": "Luật Phòng chống ma tuý 2021",
                "content": (
                    "Luật Phòng, chống ma túy 2021 (Luật số 73/2021/QH15) quy định về "
                    "phòng ngừa, ngăn chặn và đấu tranh chống tệ nạn ma túy. "
                    "Điều 3: Nghiêm cấm sản xuất, tàng trữ, vận chuyển, mua bán trái phép "
                    "chất ma túy. Điều 23: Cai nghiện bắt buộc từ 12-24 tháng."
                ),
                "type": "legal",
            },
            {
                "source": "Bộ luật Hình sự 2015",
                "content": (
                    "Bộ luật Hình sự 2015 (sửa đổi 2017) — Chương XX: Các tội phạm về ma túy. "
                    "Điều 249: Tàng trữ trái phép chất ma túy bị phạt tù từ 1-15 năm tùy lượng. "
                    "Điều 250: Vận chuyển trái phép chất ma túy bị phạt tù từ 2-20 năm. "
                    "Điều 251: Mua bán trái phép chất ma túy bị phạt tù từ 2 năm đến chung thân."
                ),
                "type": "legal",
            },
            {
                "source": "Nghị định 105/2021/NĐ-CP",
                "content": (
                    "Nghị định 105/2021/NĐ-CP hướng dẫn thi hành Luật Phòng chống ma túy. "
                    "Quy định chi tiết về: danh mục chất ma túy và tiền chất, "
                    "trình tự cai nghiện bắt buộc, quản lý sau cai."
                ),
                "type": "legal",
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
                "legal_answer": "Không tìm thấy thông tin pháp lý liên quan.",
                "sources": [],
            }

        context = "\n\n".join(
            f"[{r['source']}]\n{r['content'][:500]}" for r in results
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
            "sources": [{"source": r["source"], "content": r["content"][:200], "type": r["type"]} for r in results],
        }
