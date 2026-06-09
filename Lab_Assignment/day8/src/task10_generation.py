"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than
guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.
    Pattern: [1, 3, 5, ..., 4, 2]
    """
    if len(chunks) <= 2:
        return chunks

    reordered = []
    # Các index lẻ (1, 3, 5...) - tương ứng với score cao nhất, thứ 3, thứ 5...
    for i in range(0, len(chunks), 2):
        reordered.append(chunks[i])
    
    # Các index chẵn (2, 4...) theo thứ tự ngược lại - tương ứng với score thứ 2, thứ 4...
    # giúp đặt các kết quả tốt thứ 2 ở cuối prompt.
    for i in range(len(chunks) - 1 - (len(chunks) % 2 == 0), 0, -2):
        reordered.append(chunks[i])

    return reordered


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation using real LLMs.
    """
    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)
    
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 2: Reorder
    reordered = reorder_for_llm(chunks)
    
    # Step 3: Format context
    context = format_context(reordered)
    
    # Step 4: Build prompt
    prompt = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    
    # Step 5: Call LLM based on provider
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    answer = ""
    
    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
            
        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            
            model = genai.GenerativeModel(
                model_name=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
                system_instruction=SYSTEM_PROMPT
            )
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                )
            )
            answer = response.text
            
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
            )
            answer = response.content[0].text
            
        elif provider == "litellm":
            import litellm
            # Vô hiệu hóa debug output của litellm nếu không cần thiết
            litellm.suppress_debug_info = True
            
            response = litellm.completion(
                model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"), # Fallback model
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
            
        elif provider == "ollama":
            from openai import OpenAI
            # Ollama cung cấp API tương thích với OpenAI
            client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama" # api_key là bắt buộc nhưng một số setup cần chuỗi bất kỳ hợp lệ
            )
            
            response = client.chat.completions.create(
                model=os.getenv("OLLAMA_MODEL", "minimax-m3:cloud"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
            
        elif provider == "grok":
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("GROK_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
            
            response = client.chat.completions.create(
                model=os.getenv("GROK_MODEL", "grok-beta"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
            )
            answer = response.choices[0].message.content
            
        elif provider == "nvidia":
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("NVIDIA_API_KEY"),
                base_url="https://integrate.api.nvidia.com/v1",
            )
            
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
            
        else:
            answer = f"Lỗi: Provider '{provider}' không được hỗ trợ."
            
    except Exception as e:
        answer = f"Lỗi trong quá trình gọi LLM ({provider}): {e}\n\nCấu hình API Key trong file .env có thể chưa đúng."
    
    # Step 6: Return
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none"
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
