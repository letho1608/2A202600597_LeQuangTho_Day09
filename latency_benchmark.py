"""Bài Tập Cộng Điểm 2: Đo latency và đề xuất tối ưu.

Chạy:
  python latency_benchmark.py
  python latency_benchmark.py --mode stage4   # Stage 4 (in-process)
  python latency_benchmark.py --mode stage5   # Stage 5 (distributed A2A)
"""

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))


@dataclass
class BenchmarkResult:
    mode: str
    total_time: float
    steps: list[dict] = field(default_factory=list)
    error: str = ""


QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)
WARMUP_Q = "What is a contract?"


async def benchmark_stage5() -> BenchmarkResult:
    """Benchmark Stage 5 (distributed A2A via Customer Agent)."""
    import httpx

    result = BenchmarkResult(mode="Stage 5 (Distributed A2A)")
    CUSTOMER_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")

    t0 = time.time()

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        try:
            card_resp = await http_client.get(f"{CUSTOMER_URL}/.well-known/agent.json")
            card_resp.raise_for_status()
        except Exception as e:
            result.error = f"Cannot reach Customer Agent: {e}"
            result.total_time = round(time.time() - t0, 2)
            return result

        from a2a.types import (
            AgentCard,
            Message,
            MessageSendParams,
            Part,
            Role,
            SendMessageRequest,
            TextPart,
        )
        from a2a.client import A2AClient

        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=QUESTION))],
        )
        req = SendMessageRequest(
            id=str(time.time()),
            params=MessageSendParams(message=message),
        )

        t1 = time.time()
        response = await client.send_message(req)
        elapsed = round(time.time() - t1, 2)

        result.steps = [
            {"agent": "Customer → Law → Tax + Compliance", "time": elapsed},
        ]
        result.total_time = round(time.time() - t0, 2)

        text = _extract_text(response)
        if text:
            result.steps.append({"agent": "Response length", "time": f"{len(text)} chars"})
        return result


async def benchmark_stage4() -> BenchmarkResult:
    """Benchmark Stage 4 (in-process multi-agent)."""
    result = BenchmarkResult(mode="Stage 4 (In-Process Multi-Agent)")

    from stages.stage_4_milti_agent.main import create_graph

    graph = create_graph()

    t0 = time.time()
    try:
        res = await graph.ainvoke({
            "question": QUESTION,
            "law_analysis": "",
            "needs_tax": False,
            "needs_compliance": False,
            "tax_result": "",
            "compliance_result": "",
            "final_answer": "",
        })
        elapsed = round(time.time() - t0, 2)
        result.total_time = elapsed
        result.steps = [
            {"agent": "analyze_law", "time": "..."},
            {"agent": "check_routing", "time": "..."},
            {"agent": "call_tax + call_compliance (parallel)", "time": "..."},
            {"agent": "aggregate", "time": "..."},
        ]
        answer = res.get("final_answer", "")
        result.steps.append({"agent": "Response length", "time": f"{len(answer)} chars"})
    except Exception as e:
        result.error = str(e)
        result.total_time = round(time.time() - t0, 2)

    return result


async def benchmark_stage1() -> BenchmarkResult:
    """Benchmark Stage 1 (direct LLM) — baseline."""
    result = BenchmarkResult(mode="Stage 1 (Direct LLM — Baseline)")

    from common.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm()
    t0 = time.time()
    try:
        resp = await llm.ainvoke([
            SystemMessage(content="You are a legal expert. Answer concisely."),
            HumanMessage(content=QUESTION),
        ])
        elapsed = round(time.time() - t0, 2)
        result.total_time = elapsed
        result.steps = [
            {"agent": "Single LLM call", "time": f"{elapsed}s"},
            {"agent": "Response length", "time": f"{len(resp.content)} chars"},
        ]
    except Exception as e:
        result.error = str(e)
        result.total_time = round(time.time() - t0, 2)

    return result


def _extract_text(response: object) -> str:
    if hasattr(response, "root"):
        response = response.root
    result = getattr(response, "result", None)
    if result is None:
        return ""
    artifacts = getattr(result, "artifacts", None)
    if artifacts:
        text = ""
        for artifact in artifacts:
            for part in getattr(artifact, "parts", []) or []:
                text += _part_text(part)
        if text:
            return text
    parts = getattr(result, "parts", None)
    if parts:
        text = ""
        for part in parts:
            text += _part_text(part)
        return text
    history = getattr(result, "history", None)
    if history:
        text = ""
        for msg in history:
            for part in getattr(msg, "parts", []) or []:
                text += _part_text(part)
        return text
    return ""


def _part_text(part: object) -> str:
    inner = getattr(part, "root", part)
    return getattr(inner, "text", "") or ""


def print_report(results: list[BenchmarkResult]):
    """In báo cáo so sánh latency."""
    print("=" * 75)
    print("  BÁO CÁO ĐO LATENCY — LEGAL MULTI-AGENT SYSTEM")
    print("=" * 75)
    print(f"  Câu hỏi: {QUESTION[:80]}...")
    print(f"  Provider: {os.getenv('LLM_PROVIDER', 'openrouter')}")
    print(f"  Model: {os.getenv('LLM_MODEL') or os.getenv('OPENROUTER_MODEL', '(default)')}")
    print("=" * 75)
    print()

    # Sort by time
    results.sort(key=lambda r: r.total_time)

    for r in results:
        status = "✅" if not r.error else "❌"
        print(f"  {status} {r.mode}")
        print(f"     Tổng thời gian: {r.total_time}s")
        if r.error:
            print(f"     Lỗi: {r.error}")
        for s in r.steps:
            print(f"     ├─ {s['agent']}: {s['time']}")
        print()

    # Comparison
    print("-" * 75)
    print("  SO SÁNH")
    print("-" * 75)
    if len(results) >= 2 and not any(r.error for r in results[:2]):
        fastest = results[0]
        slowest = results[-1]
        ratio = slowest.total_time / fastest.total_time if fastest.total_time > 0 else 0
        print(f"  Nhanh nhất:  {fastest.mode} ({fastest.total_time}s)")
        print(f"  Chậm nhất:  {slowest.mode} ({slowest.total_time}s)")
        print(f"  Chênh lệch: {ratio:.1f}x")

    print()
    print("=" * 75)
    print("  ĐỀ XUẤT GIẢM LATENCY")
    print("=" * 75)
    print()
    suggestions = [
        ("1. Dùng Stage 4 (in-process) thay vì Stage 5 (distributed)",
         "Loại bỏ HTTP overhead, gọi function trực tiếp. "
         "Giảm ~30-50% latency."),
        ("2. Chọn model nhanh hơn",
         "Dùng LLM_MODEL=openai/gpt-4o-mini hoặc "
         "llama-3.1-8b thay vì Claude Sonnet. "
         "Giảm ~40-60% latency."),
        ("3. Cache kết quả cho câu hỏi trùng",
         "Dùng in-memory cache (dict) key = hash(question + model). "
         "Giảm ~100% latency cho repeated queries."),
        ("4. Streaming response",
         "A2A hỗ trợ streaming — user thấy kết quả từng phần "
         "thay vì chờ đầy đủ. Cải thiện perceived latency."),
        ("5. Tối ưu parallel execution",
         "Tax + Compliance agents đã chạy song song. "
         "Có thể thêm timeout từng agent để tránh chờ agent chậm."),
        ("6. Dùng Ollama local (nếu có GPU)",
         "Loại bỏ network latency, phù hợp cho development. "
         "Giảm ~20-40% latency."),
    ]
    for title, detail in suggestions:
        print(f"  {title}")
        print(f"     {detail}")
        print()

    print("=" * 75)
    print("  KẾT LUẬN")
    print("=" * 75)
    print()
    print("  Tổng thời gian xử lý phụ thuộc vào:")
    print("  - Số lượng agents tham gia (3-5 agents)")
    print("  - Model speed (LLM call chiếm ~80% thời gian)")
    print("  - Network latency (nếu dùng API remote)")
    print("  - Kích thước response (response càng dài càng chậm)")
    print()
    print("  Khuyến nghị: Với production, kết hợp nhiều phương án")
    print("  (model nhanh + caching + streaming) để đạt latency < 10s.")
    print("=" * 75)


async def main():
    parser = argparse.ArgumentParser(description="Latency Benchmark")
    parser.add_argument("--mode", choices=["all", "stage1", "stage4", "stage5"], default="all")
    args = parser.parse_args()

    os.environ["LLM_PROVIDER"] = os.getenv("LLM_PROVIDER", "openrouter")

    results = []

    if args.mode in ("all", "stage1"):
        print("\n[1/3] Benchmarking Stage 1 (Direct LLM)...")
        r = await benchmark_stage1()
        results.append(r)
        print(f"  Done: {r.total_time}s{' (error)' if r.error else ''}")

    if args.mode in ("all", "stage4"):
        print("\n[2/3] Benchmarking Stage 4 (In-Process Multi-Agent)...")
        r = await benchmark_stage4()
        results.append(r)
        print(f"  Done: {r.total_time}s{' (error)' if r.error else ''}")

    if args.mode in ("all", "stage5"):
        print("\n[3/3] Benchmarking Stage 5 (Distributed A2A)...")
        r = await benchmark_stage5()
        results.append(r)
        print(f"  Done: {r.total_time}s{' (error)' if r.error else ''}")

    print()
    print_report(results)


if __name__ == "__main__":
    asyncio.run(main())
