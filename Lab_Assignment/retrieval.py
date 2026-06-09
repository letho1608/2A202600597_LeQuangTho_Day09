"""Retrieval pipeline — imports Day 8's RAG pipeline with graceful fallback.

Day 8's full RAG pipeline (chromadb, sentence-transformers, BM25, reranking) is loaded
if available. Otherwise falls back to keyword search on the standardized data files.

To enable full pipeline:
  git clone https://github.com/letho1608/2A202600597_LeQuangTho_Day8.git day8
  pip install -r day8/requirements.txt
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "standardized"
DAY8_DIR = Path(__file__).parent / "day8"


def load_documents(doc_type: str = "legal") -> list[dict]:
    """Load markdown files for a given domain (legal/news)."""
    base = DATA_DIR / doc_type
    if not base.exists():
        return []
    docs = []
    for f in sorted(base.glob("*.md")):
        try:
            docs.append({
                "source": f.stem,
                "content": f.read_text(encoding="utf-8"),
                "type": doc_type,
            })
        except Exception:
            pass
    return docs


def keyword_search(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    """Simple keyword-based search fallback."""
    q = query.lower()
    scored = []
    for doc in documents:
        score = sum(1 for kw in q.split() if kw in doc["content"].lower())
        if score > 0:
            scored.append({**doc, "score": score / max(len(q.split()), 1)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def retrieve(query: str, doc_type: str = "legal", top_k: int = 5) -> list[dict]:
    """Retrieve chunks using Day 8 pipeline or fallback to keyword search."""
    documents = load_documents(doc_type)
    if not documents:
        return []

    if DAY8_DIR.exists():
        import sys
        sys.path.insert(0, str(DAY8_DIR))
        try:
            from day8.src.task9_retrieval_pipeline import retrieve as day8_retrieve
            results = day8_retrieve(query, top_k=top_k)
            if results:
                return results
        except Exception:
            pass

    return keyword_search(query, documents, top_k=top_k)
