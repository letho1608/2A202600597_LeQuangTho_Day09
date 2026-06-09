"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"

from pageindex import PageIndexClient

def upload_documents():
    """
    Upload toàn bộ raw documents (PDF) lên PageIndex.
    """
    if not PAGEINDEX_API_KEY:
        print("⚠ PAGEINDEX_API_KEY is missing!")
        return

    pi = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    
    # PageIndex yêu cầu PDF. Ta scan LANDING_DIR
    for doc_file in LANDING_DIR.rglob("*"):
        if doc_file.suffix.lower() == ".pdf":
            try:
                pi.submit_document(file_path=str(doc_file))
                print(f"  ✓ Uploaded: {doc_file.name}")
            except Exception as e:
                print(f"  ✗ Error uploading {doc_file.name}: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex API thật.
    Note: PageIndex submit_query yêu cầu doc_id cụ thể.
    Để làm 'vectorless RAG' chung cho cả kho dữ liệu, ta cần lấy doc_id từ list_documents.
    """
    if not PAGEINDEX_API_KEY:
        print("⚠ PAGEINDEX_API_KEY is missing!")
        return []

    pi = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    
    try:
        # Lấy danh sách documents đã upload để lấy IDs
        docs_resp = pi.list_documents(limit=10)
        doc_list = docs_resp.get("documents", [])
        
        all_results = []
        for doc in doc_list[:3]: # Giới hạn 3 docs đầu để tránh rate limit hoặc quá chậm
            doc_id = doc.get("id")
            if not doc_id: continue
            
            try:
                # Query từng document
                res = pi.submit_query(doc_id=doc_id, query=query)
                # Parse kết quả tùy theo cấu trúc trả về (giả định có trường 'answer' hoặc 'content')
                content = res.get("answer", str(res))
                all_results.append({
                    "content": content,
                    "score": 0.9, # PageIndex thường trả về answer trực tiếp
                    "metadata": {"doc_id": doc_id, "filename": doc.get("filename")},
                    "source": "pageindex"
                })
            except Exception as e:
                print(f"  ✗ Error querying doc {doc_id}: {e}")

        return all_results[:top_k]
    except Exception as e:
        print(f"  ✗ PageIndex search error: {e}")
        return []


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
