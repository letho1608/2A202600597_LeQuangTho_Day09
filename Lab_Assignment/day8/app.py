import streamlit as st
import os
import sys

# Đảm bảo có thể import thư mục src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task10_generation import generate_with_citation

st.set_page_config(page_title="RAG Chatbot - Luật Ma Túy", page_icon="⚖️", layout="wide")

st.title("⚖️ Trợ Lý Pháp Lý - Luật Phòng Chống Ma Túy")
st.markdown("Hệ thống RAG tra cứu văn bản pháp luật và tin tức về nghệ sĩ vi phạm ma túy.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Nhập câu hỏi mới
if prompt := st.chat_input("Nhập câu hỏi của bạn (vd: Hình phạt cho tội tàng trữ ma túy?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm thông tin và tổng hợp..."):
            try:
                # Gọi hàm generation đã được cấu hình trong task 10
                result = generate_with_citation(prompt)
                
                answer = result.get("answer", "Lỗi: Không có câu trả lời.")
                sources = result.get("sources", [])
                retrieval_source = result.get("retrieval_source", "none")
                
                st.markdown(answer)
                
                # Hiển thị nguồn
                if sources:
                    with st.expander(f"📚 Nguồn tham khảo ({len(sources)} tài liệu - Nguồn: {retrieval_source})"):
                        for i, doc in enumerate(sources, 1):
                            source_name = doc['metadata'].get('source', 'Unknown')
                            doc_type = doc['metadata'].get('type', 'unknown')
                            st.markdown(f"**{i}. {source_name} ({doc_type})** - Score: {doc.get('score', 0):.3f}")
                            st.caption(f"{doc['content'][:300]}...")
                            
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")
