# Lab Assignment — Supervisor-Workers Pattern

Improves **Day 8's RAG pipeline** với **Supervisor-Workers** multi-agent architecture.

## Architecture

```
User Question
    ↓
Supervisor (LLM classification: legal / news / both)
    ├──→ Legal Worker (RAG trên văn bản pháp luật)
    │         - Dùng Day 8 retrieval pipeline nếu có
    │         - Fallback: keyword search trên 3 văn bản luật
    ├──→ News Worker  (RAG trên tin tức nghệ sĩ)
    │         - Dùng Day 8 retrieval pipeline nếu có
    │         - Fallback: keyword search trên 5 bài báo
    └──→ Synthesis Worker (tổng hợp + citation)
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

### Basic (fallback search)
```bash
streamlit run Lab_Assignment/app.py
```

### Với Day 8 RAG pipeline đầy đủ
```bash
# Clone Day 8 repo
git clone https://github.com/letho1608/2A202600597_LeQuangTho_Day8.git day8

# Install Day 8 dependencies
pip install -r day8/requirements.txt

# Chạy pipeline indexing (nếu chưa có chroma_db)
cd day8
python -m src.task4_chunking_indexing
cd ..

# Start app
streamlit run Lab_Assignment/app.py
```

## Worker Pattern

- Supervisor dùng LangGraph `Send()` API để dispatch workers song song
- Mỗi worker là một `StateGraph` node riêng biệt
- Synthesis worker aggregate kết quả từ nhiều workers
- Sources được tự động merge bằng reducer `Annotated[list[dict], _merge]`

## Cải tiến so với Day 8

| Day 8 | Lab_Assignment |
|-------|---------------|
| RAG pipeline đơn (retrieve → generate) | Supervisor-Workers pattern (phân loại → chuyên gia → tổng hợp) |
| Tất cả query qua 1 pipeline | Router thông minh: legal/news/both |
| Citation trong generation | Citation từ synthesis worker riêng |
| Thiếu parallelism | Legal + News chạy song song qua `Send()` |
| - | Có fallback keyword search khi thiếu dependencies |
