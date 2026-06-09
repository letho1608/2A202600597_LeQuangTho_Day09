# Lab Solution — Day 09

## Bài Tập 2: Tools và Knowledge Base

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
    """Kiểm tra thời hiệu khởi kiện theo loại vụ án."""
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

if tool_call["name"] == "search_legal_knowledge":
    tool_result = search_legal_knowledge.invoke(tool_call["args"])
elif tool_call["name"] == "check_statute_of_limitations":
    tool_result = check_statute_of_limitations.invoke(tool_call["args"])
```

---

## Bài Tập 4: Multi-Agent với Privacy Agent

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

### 2. Thêm conditional routing

```python
def check_routing(state: State) -> list[Send]:
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

### 3. Cập nhật graph

```python
graph.add_node("privacy_agent", privacy_agent)
graph.add_edge("privacy_agent", "aggregate_results")
```

---

## Câu Hỏi Ôn Tập

### 1. Single agent vs Multi-agent?
- **Single agent**: tác vụ đơn giản, 1 domain, chi phí thấp
- **Multi-agent**: nhiều chuyên môn, xử lý song song, dễ mở rộng

### 2. A2A vs REST/gRPC?
A2A chuẩn hóa Agent Card, Message format, discovery tích hợp, tracing built-in, task-based.

### 3. Prevent infinite delegation loops?
Depth guard (`MAX_DELEGATION_DEPTH`), visited tracking, timeout, circuit breaker.

### 4. Tại sao cần Registry?
Dynamic discovery, load balancing, health checks, scalability — không hardcode URLs.
