"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

from typing import Optional


from sentence_transformers import CrossEncoder

def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Cross-Encoder model (Local).
    """
    if not candidates:
        return []

    # Sử dụng model multilingual nhẹ và hiệu quả
    model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
    
    # Chuẩn bị cặp (query, document)
    pairs = [[query, c["content"]] for c in candidates]
    
    # Dự đoán scores
    scores = model.predict(pairs)
    
    # Cập nhật scores và sắp xếp
    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = float(score)
        # Giữ lại score cũ nếu cần, nhưng ưu tiên rerank_score cho việc sort
        candidates[i]["score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.
    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    rrf_scores = {}  # content -> score
    content_map = {}  # content -> full dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)
            if key not in content_map:
                content_map[key] = item
            else:
                content_map[key]["metadata"].update(item["metadata"])

    # Sort by RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = float(score)
        results.append(item)

    return results


def rerank_simple(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Một bản rerank đơn giản bằng cách sort lại candidates.
    """
    sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_candidates[:top_k]


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # Chuyển mặc định sang cross_encoder
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if method == "cross_encoder":
        try:
            return rerank_cross_encoder(query, candidates, top_k)
        except Exception as e:
            print(f"  ✗ Cross-Encoder error: {e}. Falling back to simple.")
            return rerank_simple(query, candidates, top_k)
    elif method == "simple":
        return rerank_simple(query, candidates, top_k)
    else:
        return rerank_simple(query, candidates, top_k)


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
