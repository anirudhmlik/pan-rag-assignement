import streamlit as st
import requests
import os
import shutil

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="🧠 RAG Assistant", layout="wide")

st.title("🧠 RAG Document QA System")

# --- Section: Upload + Reset ---
st.markdown("## 🔄 Document Management")

col1, col2 = st.columns(2)

with col1:
    # Upload Section
    st.subheader("📤 Upload Documents")
    MAX_FILES = 20

    uploaded_files = st.file_uploader(  
    f"Upload PDF/TXT files (Max {MAX_FILES})",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

    # File count enforcement
    if uploaded_files:  
        num_files = len(uploaded_files)
        st.info(f"📄 You selected {num_files} file(s).")
        if num_files > MAX_FILES:
            st.warning(f"⚠️ Limit is {MAX_FILES} files. Please remove {num_files - MAX_FILES} file(s).")
            upload_enabled = False
        else:
            upload_enabled = True
    else:
        upload_enabled = False

    if st.button("🚀 Upload", disabled=not upload_enabled):
        if uploaded_files:
            progress_text = st.empty()
            progress_bar = st.progress(0)
        
            files = []
            for idx, file in enumerate(uploaded_files):
                files.append(("files", (file.name, file, "application/pdf")))
                progress = int(((idx + 1) / len(uploaded_files)) * 100)
                progress_bar.progress(progress)
            progress_text.text(f"Uploading {idx + 1} of {len(uploaded_files)}...")

            try:
                res = requests.post(f"{API_BASE}/upload/documents", files=files)
                st.success("✅ Upload complete")
                st.json(res.json())
            except Exception as e:
                st.error(f"❌ Upload failed: {e}")
        else:
            st.warning("⚠️ Please select at least one file to upload.")

with col2:
    left_col, right_col = st.columns([1, 2])  # Wider left, narrow right
    
    with right_col:
        st.markdown("### 🧹 Reset Vector Store & Database")
        if st.button("🗑️ Delete All Data"):
            vector_dir = "vector_db_data/faiss_index"
            if os.path.exists(vector_dir):
                shutil.rmtree(vector_dir)
                st.success("🗑️ Vector index deleted.")
            else:
                st.warning("⚠️ No vector index found.")

            st.info("ℹ️ To fully reset metadata DB, run: `docker-compose down --volumes` → `docker-compose up -d`")

# --- Section: Query Interface ---
st.divider()
st.markdown("## ❓ Ask a Question")

query_col1, query_col2 = st.columns([3, 1])
with query_col1:
    query_text = st.text_input("🔍 Your Query", placeholder="e.g., What projects has Anirudh worked on?")
with query_col2:
    top_k = st.slider("🔢 Top K", 1, 20, value=4)

if st.button("🧠 Get Answer"):
    if query_text.strip() == "":
        st.warning("⚠️ Query cannot be empty.")
    else:
        payload = {"query": query_text, "top_k": top_k}
        response = requests.post(f"{API_BASE}/query/ask", json=payload)

        if response.status_code == 200:
            data = response.json()
            with st.container():
                st.success("✅ Answer:")
                st.write(data.get("response"))

                st.markdown("---")
                st.markdown("### 📄 Retrieved Sources")
                for src in data.get("retrieved_sources", []):
                    st.markdown(f"""
                    - **Document:** {src.get('doc_title')}
                    - **Page:** {src.get('page_number')}, **Chunk:** {src.get('chunk_index')}
                    """)

        else:
            st.error(f"❌ Error {response.status_code}")
            st.json(response.json())

# --- Section: Admin & Debug ---
st.divider()
st.markdown("## 🛠️ Admin Panel")

with st.expander("📑 Uploaded Document Metadata"):
    try:
        response = requests.get(f"{API_BASE}/documents/metadata")
        if response.status_code == 200:
            docs = response.json()
            if docs:
                st.write("**Documents in DB:**")
                st.dataframe(docs)
            else:
                st.info("No documents uploaded.")
        else:
            st.error(f"Error: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error fetching metadata: {e}")

with st.expander("📜 Query History"):
    try:
        response = requests.get(f"{API_BASE}/query/history")
        if response.status_code == 200:
            history = response.json()
            if history:
                st.dataframe(history)
            else:
                st.info("No past queries yet.")
        else:
            st.error(f"Error: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Could not fetch query history: {e}")