"""Demo Web Server — port 8080.

A web UI that visualises agent interactions for the Legal Multi-Agent System.
Supports both Stage 5 (distributed A2A) and Stage 4 (in-process) modes.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from uuid import uuid4

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [demo_web] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal Multi-Agent Demo", version="1.0.0")

HERE = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))

static_dir = os.path.join(HERE, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/ask")
async def ask_question(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    mode = body.get("mode", "stage5")

    if not question:
        return JSONResponse({"error": "Question is required"}, status_code=400)

    steps = []
    total_start = time.time()

    try:
        if mode == "stage4":
            result, steps = await _run_stage4(question)
        else:
            result, steps = await _run_stage5(question)

        total_time = round(time.time() - total_start, 2)
        return JSONResponse({
            "answer": result,
            "steps": steps,
            "total_time": total_time,
            "mode": mode,
        })

    except Exception as exc:
        logger.exception("Request failed: %s", exc)
        total_time = round(time.time() - total_start, 2)
        return JSONResponse({
            "error": str(exc),
            "steps": steps,
            "total_time": total_time,
            "mode": mode,
        }, status_code=500)


async def _run_stage5(question: str) -> tuple[str, list]:
    """Call the Customer Agent A2A service (Stage 5)."""
    steps = []
    steps.append({"agent": "user", "action": "Gửi câu hỏi", "status": "done", "time": 0})

    t0 = time.time()
    async with httpx.AsyncClient(timeout=300.0) as http_client:
        steps.append({"agent": "customer", "action": "Kết nối Customer Agent...", "status": "running", "time": 0})

        card_url = f"{CUSTOMER_AGENT_URL}/.well-known/agent.json"
        card_resp = await http_client.get(card_url)
        card_resp.raise_for_status()
        steps[-1]["status"] = "done"
        steps[-1]["time"] = round(time.time() - t0, 2)

        from a2a.types import AgentCard, Message, Part, Role, TextPart, MessageSendParams
        from a2a.client import A2AClient

        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
        )
        request = MessageSendParams(message=message)
        from a2a.types import SendMessageRequest
        req = SendMessageRequest(id=str(uuid4()), params=request)

        steps.append({"agent": "law", "action": "Law Agent phân tích...", "status": "running", "time": 0})
        steps.append({"agent": "tax", "action": "Tax Agent xử lý...", "status": "pending", "time": 0})
        steps.append({"agent": "compliance", "action": "Compliance Agent xử lý...", "status": "pending", "time": 0})

        t1 = time.time()
        response = await client.send_message(req)
        elapsed = round(time.time() - t1, 2)

        steps[-3]["status"] = "done"
        steps[-3]["time"] = elapsed
        steps[-2]["status"] = "done"
        steps[-2]["time"] = elapsed
        steps[-1]["status"] = "done"
        steps[-1]["time"] = elapsed

        from a2a.types import SendMessageResponse
        result_text = _extract_text(response)
        if not result_text:
            result_text = "Không nhận được phản hồi từ hệ thống."

        steps.append({"agent": "response", "action": "Tổng hợp kết quả", "status": "done", "time": elapsed})
        return result_text, steps


async def _run_stage4(question: str) -> tuple[str, list]:
    """Run the Stage 4 multi-agent graph in-process."""
    steps = []
    steps.append({"agent": "user", "action": "Gửi câu hỏi", "status": "done", "time": 0})

    import sys
    sys.path.insert(0, os.path.join(HERE, ".."))

    from stages.stage_4_milti_agent.main import create_graph

    graph = create_graph()

    t0 = time.time()
    steps.append({"agent": "law", "action": "Law Agent phân tích...", "status": "running", "time": 0})
    steps.append({"agent": "tax", "action": "Tax Agent xử lý...", "status": "pending", "time": 0})
    steps.append({"agent": "compliance", "action": "Compliance Agent xử lý...", "status": "pending", "time": 0})

    result = await graph.ainvoke({
        "question": question,
        "law_analysis": "",
        "needs_tax": False,
        "needs_compliance": False,
        "tax_result": "",
        "compliance_result": "",
        "final_answer": "",
    })

    elapsed = round(time.time() - t0, 2)
    steps[-3]["status"] = "done"
    steps[-3]["time"] = elapsed
    steps[-2]["status"] = "done"
    steps[-2]["time"] = elapsed
    steps[-1]["status"] = "done"
    steps[-1]["time"] = elapsed

    answer = result.get("final_answer", "") or "Không có kết quả."
    steps.append({"agent": "response", "action": "Tổng hợp kết quả", "status": "done", "time": elapsed})
    return answer, steps


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


async def serve(port: int = 8080) -> None:
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    logger.info("Starting Demo Web Server on port 8080")
    asyncio.run(serve())
