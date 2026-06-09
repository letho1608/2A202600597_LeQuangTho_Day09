# Đáp Án Bài Tập

## Exercise 2: Tools và Knowledge Base

### 1. Thêm entry về luật lao động vào `LEGAL_KNOWLEDGE`

```python
LEGAL_KNOWLEDGE = [
    {
        "id": "ucc_breach",
        "keywords": ["breach", "contract", "remedies", "damages", "ucc"],
        "text": (
            "Under the Uniform Commercial Code (UCC) Article 2, remedies for breach of contract "
            "include: (1) expectation damages; (2) consequential damages; (3) specific performance; "
            "(4) cover damages. Statute of limitations is typically 4 years (UCC § 2-725)."
        ),
    },
    {
        "id": "labor_law",
        "keywords": ["lao động", "sa thải", "hợp đồng lao động", "labor", "termination"],
        "text": (
            "Theo Bộ luật Lao động Việt Nam 2019, người sử dụng lao động có thể "
            "đơn phương chấm dứt hợp đồng trong các trường hợp: (1) người lao động "
            "thường xuyên không hoàn thành công việc; (2) bị ốm đau, tai nạn đã điều trị "
            "12 tháng chưa khỏi; (3) thiên tai, hỏa hoạn; (4) người lao động đủ tuổi nghỉ hưu."
        ),
    },
]
```

### 2. Tạo tool `check_statute_of_limitations`

```python
@tool
def check_statute_of_limitations(case_type: str) -> str:
    """Kiểm tra thời hiệu khởi kiện theo loại vụ án.

    Args:
        case_type: Loại vụ án (contract, tort, property, labor)
    """
    limits = {
        "contract": "4 năm (UCC § 2-725)",
        "tort": "2-3 năm tùy theo tiểu bang",
        "property": "5 năm",
        "labor": "2 năm theo Bộ luật Lao động Việt Nam 2019",
    }
    result = limits.get(case_type.lower(), "Không xác định — cần tham vấn luật sư")
    return f"Thời hiệu khởi kiện cho {case_type}: {result}"
```

### 3. Cập nhật danh sách tools và xử lý tool call

```python
tools = [search_legal_knowledge, check_statute_of_limitations]
llm_with_tools = llm.bind_tools(tools)

# Trong vòng lặp xử lý tool_calls:
if tool_call["name"] == "search_legal_knowledge":
    tool_result = search_legal_knowledge.invoke(tool_call["args"])
elif tool_call["name"] == "check_statute_of_limitations":
    tool_result = check_statute_of_limitations.invoke(tool_call["args"])
```

---

## Exercise 4: Multi-Agent với Privacy Agent

### 1. Implement `privacy_agent`

```python
def privacy_agent(state: State) -> dict:
    """Agent chuyên về bảo vệ dữ liệu cá nhân và GDPR."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia về GDPR và luật bảo vệ dữ liệu cá nhân.

Câu hỏi: {state['question']}
Phân tích pháp lý: {state.get('law_analysis', 'N/A')}

Tập trung: GDPR, data protection, privacy rights, data breach, CCPA."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"privacy_analysis": response.content}
```

### 2. Thêm conditional routing cho privacy agent

```python
def check_routing(state: State) -> list[Send]:
    """Quyết định gọi agents nào dựa trên nội dung câu hỏi."""
    question_lower = state["question"].lower()
    tasks = []

    if any(kw in question_lower for kw in ["tax", "irs", "thuế"]):
        tasks.append(Send("tax_agent", state))

    if any(kw in question_lower for kw in ["compliance", "sec", "regulation"]):
        tasks.append(Send("compliance_agent", state))

    if any(kw in question_lower for kw in ["data", "privacy", "gdpr", "dữ liệu", "breach"]):
        tasks.append(Send("privacy_agent", state))

    return tasks if tasks else [Send("aggregate_results", state)]
```

### 3. Thêm privacy_agent vào graph

```python
def build_graph() -> StateGraph:
    graph = StateGraph(State)

    graph.add_node("law_agent", law_agent)
    graph.add_node("check_routing", check_routing)
    graph.add_node("tax_agent", tax_agent)
    graph.add_node("compliance_agent", compliance_agent)
    graph.add_node("privacy_agent", privacy_agent)  # THÊM
    graph.add_node("aggregate_results", aggregate_results)

    graph.add_edge(START, "law_agent")
    graph.add_edge("law_agent", "check_routing")
    graph.add_conditional_edges("check_routing", lambda x: x)
    graph.add_edge("tax_agent", "aggregate_results")
    graph.add_edge("compliance_agent", "aggregate_results")
    graph.add_edge("privacy_agent", "aggregate_results")  # THÊM
    graph.add_edge("aggregate_results", END)

    return graph.compile()
```

### 4. Thêm `privacy_analysis` vào sections trong `aggregate_results`

```python
def aggregate_results(state: State) -> dict:
    sections = []
    if state.get("law_analysis"):
        sections.append(f"📋 PHÂN TÍCH PHÁP LÝ:\n{state['law_analysis']}")
    if state.get("tax_analysis"):
        sections.append(f"💰 PHÂN TÍCH THUẾ:\n{state['tax_analysis']}")
    if state.get("compliance_analysis"):
        sections.append(f"✅ PHÂN TÍCH TUÂN THỦ:\n{state['compliance_analysis']}")
    if state.get("privacy_analysis"):
        sections.append(f"🔒 PHÂN TÍCH PRIVACY:\n{state['privacy_analysis']}")

    # ... phần còn lại giữ nguyên
```

---

## Câu Hỏi Ôn Tập

### 1. Khi nào nên dùng single agent thay vì multi-agent?

**Single agent** khi:
- Tác vụ đơn giản, chỉ cần 1 domain knowledge
- Không cần xử lý song song
- Chi phí thấp, dễ maintain
- Ví dụ: chatbot FAQ, simple Q&A

**Multi-agent** khi:
- Cần nhiều chuyên môn khác nhau (luật, thuế, compliance)
- Cần xử lý song song để giảm latency
- Hệ thống phức tạp, cần mở rộng sau này
- Ví dụ: tư vấn pháp lý toàn diện, diagnostic systems

### 2. Ưu điểm của A2A protocol so với REST/gRPC thông thường?

- **Standardized**: Agent Card, Message format chuẩn — agents từ vendors khác nhau có thể giao tiếp
- **Discovery tích hợp**: không cần hardcode URLs, agents tự tìm nhau qua Registry
- **Tracing built-in**: `trace_id` và `context_id` được propagate qua các hops
- **Task-based**: hỗ trợ async tasks, streaming, notifications
- **Extensible**: dễ thêm agents mới mà không ảnh hưởng hệ thống

### 3. Làm thế nào để prevent infinite delegation loops trong A2A?

- **Depth guard**: `MAX_DELEGATION_DEPTH = 3` — chặn delegation quá sâu
- **Visited tracking**: lưu danh sách agents đã gọi, tránh gọi lại
- **Timeout**: giới hạn thời gian cho mỗi request
- **Circuit breaker**: nếu agent liên tục fail, ngừng gọi trong khoảng thời gian

### 4. Tại sao cần Registry service? Có thể hardcode URLs không?

**Cần Registry vì:**
- **Dynamic discovery**: agents có thể thay đổi địa chỉ mà không ảnh hưởng hệ thống
- **Load balancing**: nhiều instances cho cùng 1 agent type
- **Health checks**: registry biết agent nào còn sống
- **Scalability**: thêm/bớt agents mà không cần cập nhật config

**Hardcode URLs được không?**
- Được cho hệ thống nhỏ, cố định
- Nhưng không nên vì: khó maintain, không scale được, dễ fail nếu 1 agent die

---

## Bài Tập Nâng Cao (Challenge)

### Challenge 1: Conversation Memory

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
)
# LangGraph tự động lưu conversation history qua thread_id
```

### Challenge 2: Authentication

```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
API_KEYS = {"sk-agent-key-1", "sk-agent-key-2"}

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials
```

### Challenge 3: Retry Logic

```python
import asyncio

async def delegate_with_retry(endpoint, question, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await delegate(endpoint, question, ...)
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # exponential backoff
            logger.warning(f"Retry {attempt+1}/{max_retries} after {delay}s: {exc}")
            await asyncio.sleep(delay)
    return None
```

### Challenge 4: Monitoring

```python
# Thêm metrics vào agent endpoints
from prometheus_client import Counter, Histogram, generate_latest

REQUESTS = Counter("agent_requests_total", "Total requests")
LATENCY = Histogram("agent_latency_seconds", "Request latency")
ERRORS = Counter("agent_errors_total", "Total errors")
```
