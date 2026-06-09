"""Supervisor Agent — routes questions to appropriate workers using LangGraph."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from common.llm import get_llm

from Lab_Assignment.agents.state import AgentState
from Lab_Assignment.agents.legal_worker import LegalWorker
from Lab_Assignment.agents.news_worker import NewsWorker
from Lab_Assignment.agents.synthesis_worker import SynthesisWorker


class SupervisorAgent:
    """Supervisor that delegates to specialized workers in parallel."""

    def __init__(self):
        self.llm = get_llm()
        self.legal_worker = LegalWorker()
        self.news_worker = NewsWorker()
        self.synthesis_worker = SynthesisWorker()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("supervisor", self._supervisor)
        graph.add_node("legal_worker", self.legal_worker.run)
        graph.add_node("news_worker", self.news_worker.run)
        graph.add_node("synthesis_worker", self.synthesis_worker.run)

        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", self._route, [
            "legal_worker", "news_worker", "synthesis_worker",
        ])
        graph.add_edge("legal_worker", "synthesis_worker")
        graph.add_edge("news_worker", "synthesis_worker")
        graph.add_edge("synthesis_worker", END)

        return graph.compile()

    def _supervisor(self, state: AgentState) -> dict:
        prompt = f"""Analyze this legal question and decide which specialists to consult.

Question: {state['question']}

Respond with 'legal', 'news', or 'both'. Examples:
- "What is the penalty for drug possession?" → legal
- "Which celebrity was arrested for drugs?" → news
- "What happens to celebrities caught with drugs legally?" → both"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        decision = response.content.strip().lower()
        if "both" in decision:
            decision = "both"
        elif "news" in decision:
            decision = "news"
        else:
            decision = "legal"
        return {"question": state["question"], "route_decision": decision}

    def _route(self, state: AgentState) -> list[Send]:
        d = state.get("route_decision", "legal")
        tasks = []
        if d in ("legal", "both"):
            tasks.append(Send("legal_worker", state))
        if d in ("news", "both"):
            tasks.append(Send("news_worker", state))
        if not tasks:
            tasks.append(Send("legal_worker", state))
        return tasks

    async def ask(self, question: str) -> dict:
        result = await self.graph.ainvoke({
            "question": question,
            "route_decision": "",
            "legal_answer": "",
            "news_answer": "",
            "answer": "",
            "sources": [],
        })
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
