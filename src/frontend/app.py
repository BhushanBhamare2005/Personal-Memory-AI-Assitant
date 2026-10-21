"""
Streamlit Frontend for Personal AI Memory Assistant
"""
import streamlit as st
import requests
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

# Configure page
st.set_page_config(
    page_title="Personal AI Memory Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
DEFAULT_USER_ID = "user_001"

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = DEFAULT_USER_ID
if "messages" not in st.session_state:
    st.session_state.messages = []

def make_api_call(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make an API call and report connection or server errors in the UI."""
    try:
        url = f"{API_BASE_URL}{endpoint}"

        response = requests.request(
            method,
            url,
            json=data,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Backend returned an unexpected response")
        return result
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}

# Main UI
st.title("🧠 Personal AI Memory Assistant")
st.markdown("*A futuristic AI that remembers everything about you and improves daily*")

# Sidebar
with st.sidebar:
    st.header("🧠 Personal AI Memory Assistant")

    user_id = st.text_input("User ID:", value=st.session_state.user_id)
    if user_id:
        st.session_state.user_id = user_id

    st.markdown("---")

    st.subheader("📎 Upload PDFs")
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("Index uploaded PDFs", use_container_width=True):
            try:
                api_url = f"{API_BASE_URL}/documents/upload"
                req_files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                resp = requests.post(
                    api_url,
                    params={"user_id": st.session_state.user_id},
                    files=req_files,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("success"):
                    st.success(f"Indexed {data.get('indexed', 0)} chunks from {len(uploaded_files)} PDF(s).")
                    st.session_state.pop("documents", None)
                else:
                    errors = data.get("errors", [])
                    st.error("; ".join(item.get("error", "PDF indexing failed") for item in errors))
            except Exception as e:
                st.error(f"Upload/indexing error: {e}")

    st.markdown("---")

    st.subheader("🗃️ Documents")
    if st.button("Refresh documents", use_container_width=True):
        st.session_state.pop("documents", None)

    if "documents" not in st.session_state:
        try:
            docs = make_api_call(f"/documents/list/{st.session_state.user_id}")
            st.session_state.documents = docs.get("documents", []) if isinstance(docs, dict) else []
        except Exception:
            st.session_state.documents = []

    st.write(f"Indexed documents: {len(st.session_state.documents)}")
    if st.session_state.documents:
        with st.expander("View indexed documents", expanded=False):
            for d in st.session_state.documents:
                st.caption(f"{d.get('filename')}")
                st.write(f"Chunks: {d.get('chunk_count', 'N/A')} | Pages: {d.get('total_pages', 'N/A')}")

    st.markdown("---")

    st.subheader("🧾 Memories")
    st.caption("Total memories are shown in the Memories panel.")

    st.markdown("---")

    page = st.radio("Navigate:", [
        "💬 Chat",
        "📝 Memories",
        "🔎 RAG Debug",
        "💡 Suggestions",
        "📊 Habits",
    ])


# Main Content
if page == "💬 Chat":
    st.subheader("💬 Chat with Your AI Assistant")
    st.markdown("*Powered by your personal memories and AI learning*")
    
    # Chat interface
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if prompt := st.chat_input("What would you like to talk about?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response from backend
        response_data = make_api_call(
            "/chat/send",
            method="POST",
            data={
                "user_id": st.session_state.user_id,
                "message": prompt,
                "include_memories": True
            }
        )
        
        if "assistant_response" in response_data:
            assistant_msg = response_data["assistant_response"]
            st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            
            with st.chat_message("assistant"):
                st.write(assistant_msg)
                if response_data.get("memories_used", 0) > 0:
                    st.caption(f"📚 Used {response_data['memories_used']} memories for context")

elif page == "📝 Memories":
    st.subheader("📝 Your Memories")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Memory search")
        search_query = st.text_input("Search memories:", placeholder="Find memories by meaning...")

        if search_query:
            results = make_api_call(
                "/memory/search",
                method="POST",
                data={
                    "user_id": st.session_state.user_id,
                    "query": search_query,
                    "limit": 8,
                },
            )

            if results.get("memories"):
                st.markdown(f"Found {results['count']} memories")
                for mem in results["memories"]:
                    meta = mem.get("metadata", {}) or {}
                    with st.expander(f"📌 {mem.get('content','')[:60]}..."):
                        st.write(mem.get("content", ""))
                        st.caption(
                            f"Type: {meta.get('type', 'note')} | Importance: {meta.get('importance', 'N/A')} | "
                            f"Created: {meta.get('created_at', 'N/A')}"
                        )

        st.markdown("---")
        st.markdown("### Memory timeline")
        st.info("Timeline view is based on conversation history (chat panel persists).")

    with col2:
        st.markdown("### Add memory")
        memory_content = st.text_area("Remember this:", height=120)
        memory_type = st.selectbox("Type:", ["note", "idea", "learning", "goal", "other"])

        if st.button("💾 Save Memory", use_container_width=True):
            if not memory_content.strip():
                st.warning("Enter memory content")
            else:
                result = make_api_call(
                    "/memory/add",
                    method="POST",
                    data={
                        "user_id": st.session_state.user_id,
                        "content": memory_content,
                        "memory_type": memory_type,
                    },
                )

                if result.get("success"):
                    st.success("Memory saved! 🎉")
                else:
                    st.error("Failed to save memory")


elif page == "🔎 RAG Debug":
    st.subheader("🔎 RAG Debug Panel")

    q = st.text_input("Debug query:", placeholder="Ask a question to see retrieval transparency")

    if st.button("Run retrieval", use_container_width=True):
        if not q.strip():
            st.warning("Enter a query")
        else:
            debug = make_api_call(
                "/documents_debug/debug-search",
                params={"q": q, "user_id": st.session_state.user_id},
            )
            chunks = debug.get("chunks", []) if isinstance(debug, dict) else []

            if chunks:
                with st.expander("Retrieved Document Chunks", expanded=True):
                    for i, c in enumerate(chunks, 1):
                        st.markdown(f"**{i}. {c.get('document_name','Unknown')}** (page {c.get('page_number','?')})")
                        st.caption(f"Similarity score: {c.get('similarity_score','N/A')}")
                        st.code(c.get('text','')[:600])
            elif "error" not in debug:
                st.info("No matching document chunks found.")

elif page == "💡 Suggestions":
    st.subheader("💡 Daily Suggestions")

    col1, col2, col3 = st.columns(3)

    categories = ["all", "study", "health", "productivity"]
    selected_category = st.selectbox("Filter by category:", categories)

    endpoint = f"/suggestions/daily/{st.session_state.user_id}"
    if selected_category != "all":
        endpoint += f"?category={selected_category}"

    suggestions = make_api_call(endpoint)

    if suggestions.get("suggestions"):
        for idx, sugg in enumerate(suggestions["suggestions"]):
            col = st.columns(1)[0]
            with col:
                st.markdown(f"### {sugg.get('title', 'Suggestion')}")
                st.write(sugg.get("description", ""))

                cols = st.columns(3)
                with cols[0]:
                    st.caption(f"📂 {sugg.get('category', 'general').title()}")
                with cols[1]:
                    priority = sugg.get("priority", "medium")
                    emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    st.caption(f"{emoji} {priority.title()}")
                with cols[2]:
                    if st.button("✓ Done", key=f"sugg_{idx}"):
                        st.success("Great job! 🎉")


elif page == "📊 Habits":
    st.subheader("📊 Your Habit Analysis")
    
    habits = make_api_call(f"/habits/analyze/{st.session_state.user_id}")
    
    if habits.get("habits"):
        habits_data = habits["habits"]
        
        st.markdown("### 🎯 Study Patterns")
        if "study_pattern" in habits_data:
            sp = habits_data["study_pattern"]
            st.write(f"**Frequency:** {sp.get('frequency', 'N/A')}")
            st.write(f"**Peak Hours:** {', '.join(sp.get('peak_hours', []))}")
            st.write(f"**Topics:** {', '.join(sp.get('topics', []))}")
        
        st.markdown("### 💼 Work Patterns")
        if "work_pattern" in habits_data:
            wp = habits_data["work_pattern"]
            st.write(f"**Average Hours/Day:** {wp.get('avg_hours_per_day', 'N/A')}")
            st.write(f"**Preferred Time:** {wp.get('preferred_time', 'N/A')}")
            st.write(f"**Focus Duration:** {wp.get('focus_duration', 'N/A')}")
        
        st.markdown("### 💬 Communication Style")
        if "communication_style" in habits_data:
            cs = habits_data["communication_style"]
            st.write(f"**Response Length:** {cs.get('response_length', 'N/A')}")
            st.write(f"**Preferred Topics:** {', '.join(cs.get('preferred_topics', []))}")
            st.write(f"**Tone:** {cs.get('tone', 'N/A')}")

elif page == "⚡ Quick Add":
    st.subheader("⚡ Quick Add Memory")
    
    quick_type = st.radio("What are you adding?", [
        "Quick Note",
        "Learning",
        "Goal",
        "Idea"
    ])
    
    content = st.text_area("Content:", height=150)
    
    if st.button("➕ Add", use_container_width=True):
        result = make_api_call(
            "/memory/add",
            method="POST",
            data={
                "user_id": st.session_state.user_id,
                "content": content,
                "memory_type": quick_type.lower().replace(" ", "_")
            }
        )
        
        if result.get("success"):
            st.success("✅ Added successfully!")
            st.balloons()
        else:
            st.error("❌ Failed to add")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🧠 Personal AI Memory Assistant v1.0</p>
        <p><small>Remembering everything, improving daily</small></p>
    </div>
    """,
    unsafe_allow_html=True
)
