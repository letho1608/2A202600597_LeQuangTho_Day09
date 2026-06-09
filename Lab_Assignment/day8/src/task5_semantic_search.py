"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


import chromadb
from sentence_transformers import SentenceTransformer

# Load model once
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL)

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity qua ChromaDB.
    """
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection(name="DrugLawDocs")
    except Exception as e:
        print(f"⚠ Không tìm thấy collection 'DrugLawDocs': {e}")
        return []

    # 1. Embed query
    query_embedding = model.encode(query).tolist()

    # 2. Query ChromaDB
    # ChromaDB trả về 'distances' (L2 distance mặc định). 
    # Càng nhỏ càng giống. Chúng ta chuyển sang score = 1 / (1 + distance) 
    # để có score nằm trong khoảng (0, 1] và sorted descending.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    formatted_results = []
    if results["documents"]:
        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i]
            # Chuyển distance thành score (similarity)
            # Lưu ý: ChromaDB dùng squared L2 distance mặc định.
            # Để đơn giản và đảm bảo thứ tự, ta dùng 1 / (1 + distance)
            score = 1.0 / (1.0 + distance)
            
            formatted_results.append({
                "content": results["documents"][0][i],
                "score": score,
                "metadata": results["metadatas"][0][i]
            })

    # Sắp xếp theo score giảm dần (mặc định ChromaDB đã sắp xếp theo distance tăng dần)
    return formatted_results


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
