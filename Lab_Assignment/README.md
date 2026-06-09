# Lab Assignment — Supervisor-Workers Pattern

Improves Day 8's RAG pipeline with a **Supervisor-Workers** multi-agent architecture.

## Architecture

```
User Question
    ↓
Supervisor ──→ Legal Worker (RAG on legal docs)
    │          News Worker  (RAG on news articles)
    └────────→ Synthesis Worker (combines + citations)
                    ↓
            Final Answer
```

## Components

| Agent | Role |
|-------|------|
| **Supervisor** | Phân tích câu hỏi, quyết định gọi workers nào |
| **Legal Worker** | Tra cứu văn bản pháp luật về ma túy |
| **News Worker** | Tra cứu tin tức nghệ sĩ liên quan ma túy |
| **Synthesis Worker** | Tổng hợp kết quả, format citation |

## Usage

```bash
pip install -r requirements.txt
streamlit run Lab_Assignment/app.py
```

## Worker Pattern

- Supervisor dùng LangGraph `Send()` API để dispatch workers song song
- Mỗi worker là một `StateGraph` node riêng biệt
- Synthesis worker aggregate kết quả từ nhiều workers
