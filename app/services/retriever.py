# app/services/retriever.py

import os
from typing import List, Dict
from collections import defaultdict

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangchainDocument

# Configuration
VECTOR_DB_DIRECTORY = os.getenv("VECTOR_DB_DIRECTORY", "vector_db_data/faiss_index")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Initialize Embedding Model
try:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
except Exception as e:
    print(f"[Retriever] Error loading embedding model: {e}")
    embeddings = None

def get_faiss_vector_store():
    """Loads the FAISS vector store from disk."""
    if not embeddings:
        raise ValueError("Embedding model not initialized.")

    faiss_index_path = os.path.join(VECTOR_DB_DIRECTORY, "index.faiss")
    faiss_pkl_path = os.path.join(VECTOR_DB_DIRECTORY, "index.pkl")

    if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
        print(f"[Retriever] Loading FAISS index from {VECTOR_DB_DIRECTORY}")
        return FAISS.load_local(VECTOR_DB_DIRECTORY, embeddings, allow_dangerous_deserialization=True)
    else:
        raise FileNotFoundError(f"FAISS index not found at {VECTOR_DB_DIRECTORY}. Please ingest documents first.")

async def retrieve_chunks(query_text: str, top_k: int = 4) -> List[LangchainDocument]:
    """
    Retrieves relevant document chunks from the vector database.
    """
    top_k = min(top_k, 20)
    try:
        faiss_store = get_faiss_vector_store()
        retrieved_docs = faiss_store.similarity_search(query_text, k=top_k)
        print(f"[Retriever] Retrieved {len(retrieved_docs)} chunks for query: '{query_text}'")
        return retrieved_docs
    except FileNotFoundError as e:
        print(f"[Retriever] Retrieval error: {e}")
        return []
    except Exception as e:
        raise RuntimeError(f"[Retriever] Unexpected error during retrieval: {e}")

def group_chunks_by_document(chunks: List[LangchainDocument]) -> Dict[str, List[str]]:
    grouped = defaultdict(list)
    for chunk in chunks:
        doc_id = chunk.metadata.get("document_id", "Unknown Document")
        filename = chunk.metadata.get("filename", doc_id)
        grouped[filename].append(chunk.page_content)
    return grouped

def format_comparison_prompt(grouped_chunks: Dict[str, List[str]], query: str) -> str:
    prompt = ""
    for idx, (filename, texts) in enumerate(grouped_chunks.items(), 1):
        prompt += f"\nDocument {idx} ({filename}):\n"
        for text in texts:
            prompt += f"- {text.strip()}\n"
    prompt += f"\n\nQuestion: {query.strip()}"
    return prompt