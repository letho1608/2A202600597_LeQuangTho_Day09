"""Synthesis Worker — combines results from all workers into final answer."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState


class SynthesisWorker:
    """Combines legal + news analysis into a coherent final answer."""

    def __init__(self):
        self.llm = get_llm()

    def run(self, state: AgentState) -> dict:
        legal = state.get("legal_answer", "")
        news = state.get("news_answer", "")
        sources = state.get("sources", [])

        parts = []
        if legal:
            parts.append(f"=== PHÂN TÍCH PHÁP LÝ ===\n{legal}")
        if news:
            parts.append(f"=== TIN TỨC LIÊN QUAN ===\n{news}")

        if not parts:
            return {
                "answer": "Không tìm thấy thông tin liên quan từ các nguồn hiện có.",
                "sources": [],
            }

        combined = "\n\n".join(parts)
        source_list = "\n".join(
            f"- {s['source']} ({s.get('type', 'unknown')})" for s in sources if s.get("source")
        )

        prompt = f"""Tổng hợp các phân tích dưới đây thành một câu trả lời hoàn chỉnh, có cấu trúc rõ ràng.

{combined}

Nguồn tham khảo:
{source_list}

Yêu cầu:
1. Trình bày rõ ràng, có đề mục nếu cần
2. Mỗi luận điểm phải có citation [Nguồn]
3. Nếu thông tin mâu thuẫn giữa các nguồn, nêu rõ
4. Phân biệt rõ thông tin pháp lý và tin tức"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"answer": response.content, "sources": sources}
