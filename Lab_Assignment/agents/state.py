"""Agent State definition — shared across all agents."""

from typing import Annotated
from typing_extensions import TypedDict


def _merge(left: list | None, right: list | None) -> list:
    return (left or []) + (right or [])


class AgentState(TypedDict):
    question: str
    route_decision: str
    legal_answer: str
    news_answer: str
    answer: str
    sources: Annotated[list[dict], _merge]
