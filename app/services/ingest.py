# app/services/ingest.py

from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Tuple
import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings # For local models
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangchainDocument

from app.models.metadata import SessionLocal, Document, Chunk
from sqlalchemy.orm import Session
from sqlalchemy import exc

# Configuration
# Change VECTOR_DB_PATH to be just the directory name
VECTOR_DB_DIRECTORY = os.getenv("VECTOR_DB_PATH", "vector_db_data/faiss_index")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Ensure the vector DB directory exists
os.makedirs(VECTOR_DB_DIRECTORY, exist_ok=True)


def _clean_text(text: str) -> str:
    """
    Cleans the input text by removing common OCR/PDF extraction artifacts and standardizing.
    """
    # ... (rest of the _clean_text function remains unchanged)
    cleaned_text = text.replace('♂phone', 'Phone: ')
    cleaned_text = cleaned_text.replace('/envel⌢p', 'Email: ') # Combine /envel and ⌢p
    cleaned_text = cleaned_text.replace('/linkedin', 'LinkedIn: ')
    cleaned_text = cleaned_text.replace('/github', 'GitHub: ')
    cleaned_text = cleaned_text.replace('♂¶ap-¶arker-alt', 'Location: ')
    cleaned_text = cleaned_text.replace('/char◎-line', '') # Remove interest icon
    cleaned_text = cleaned_text.replace('/brain', '') # Remove interest icon
    cleaned_text = cleaned_text.replace('/code-branch', '') # Remove interest icon
    cleaned_text = cleaned_text.replace('♂project-diagra¶', '') # Remove interest icon
    cleaned_text = cleaned_text.replace('♂robot', '') # Remove interest icon
    cleaned_text = cleaned_text.replace('¨', '') # Remove diacritic for "Schrödinger"
    cleaned_text = cleaned_text.replace('´', '') # Remove diacritic for "Schrödinger"
    cleaned_text = cleaned_text.replace('˜', '') # Remove diacritic or other artifacts

    # 2. Remove any remaining non-ASCII characters that are not basic punctuation or whitespace
    # This regex keeps alphanumeric characters, spaces, and common punctuation.
    # Adjust if you have specific foreign language characters that *should* be preserved.
    cleaned_text = re.sub(r'[^\x20-\x7E\n\r]+', ' ', cleaned_text)

    # 3. Normalize whitespace: multiple spaces to single space, remove leading/trailing whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text


# Initialize Embedding Model (load once)
try:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
except Exception as e:
    print(f"Error loading embedding model: {e}")
    embeddings = None # Handle this gracefully in your app


def get_faiss_vector_store():
    """Initializes or loads the FAISS vector store."""
    if not embeddings:
        raise ValueError("Embedding model not initialized.")

    # Check for the existence of the FAISS files within the directory
    # Langchain's FAISS.load_local expects the directory path, and it will look for
    # 'index.faiss' and 'index.pkl' (or similar) inside that directory.
    faiss_index_file = os.path.join(VECTOR_DB_DIRECTORY, "index.faiss")
    faiss_pkl_file = os.path.join(VECTOR_DB_DIRECTORY, "index.pkl")

    if os.path.exists(faiss_index_file) and os.path.exists(faiss_pkl_file):
        print(f"Loading existing FAISS index from {VECTOR_DB_DIRECTORY}")
        # Pass the directory path to load_local
        return FAISS.load_local(VECTOR_DB_DIRECTORY, embeddings, allow_dangerous_deserialization=True)
    else:
        print(f"Creating new FAISS index at {VECTOR_DB_DIRECTORY}")
        # Initialize with a dummy text, then save to establish the files
        # It's important to save it so subsequent calls can load it
        new_faiss_store = FAISS.from_texts(["initialization"], embeddings)
        new_faiss_store.save_local(VECTOR_DB_DIRECTORY) # Save the initial empty store
        return new_faiss_store


async def process_document(file_content: bytes, filename: str) -> Dict:
    """
    Ingests a document: loads, chunks, embeds, and stores in vector DB and metadata DB.
    """
    db: Session = SessionLocal() # Use SessionLocal directly without 'with' for now, to ensure finally block handles close
    document_id = str(uuid4())
    doc_metadata = None

    print(f"[{datetime.utcnow()}] Starting processing for document: {filename}")

    try:
        temp_file_path = f"/tmp/{filename}"
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        print(f"[{datetime.utcnow()}] Temporary file saved: {temp_file_path}")

        loader = PyPDFLoader(temp_file_path)
        pages = loader.load()
        num_pages = len(pages) if pages else 0
        print(f"[{datetime.utcnow()}] Loaded {num_pages} pages from {filename}")

        # Create new document record in DB
        doc_metadata = Document(
            id=document_id,
            filename=filename,
            uploaded_at=datetime.utcnow(),
            num_pages=num_pages,
            status="processing"
        )
        db.add(doc_metadata)
        print(f"[{datetime.utcnow()}] Added document metadata to session. Document ID: {document_id}")
        db.commit() # Commit here to persist the initial 'processing' status
        db.refresh(doc_metadata)
        print(f"[{datetime.utcnow()}] Committed initial document status to DB.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks: List[LangchainDocument] = []
        for i, page in enumerate(pages):
            cleaned_page_content = _clean_text(page.page_content)
            cleaned_page_doc = LangchainDocument(page_content=cleaned_page_content, metadata=page.metadata)
            page_chunks = text_splitter.split_documents([cleaned_page_doc])
            for chunk_idx, pc in enumerate(page_chunks):
                pc.metadata.update({
                    "source": filename,
                    "document_id": document_id,
                    "chunk_index": chunk_idx,
                    "page_number": page.metadata.get("page", i),  # fallback to index if missing
                    "doc_title": os.path.splitext(filename)[0].replace("_", " ").title()
                })
                chunks.append(pc)
        print(f"[{datetime.utcnow()}] Split document into {len(chunks)} chunks.")

        if not embeddings:
            raise ValueError("Embedding model not loaded. Cannot process document.")

        # Load or initialize vector store
        try:
            faiss_store = get_faiss_vector_store()
            print(f"[{datetime.utcnow()}] FAISS store loaded from disk.")
        except Exception as e:
            print(f"[{datetime.utcnow()}] No existing FAISS store found or error: {e}. Creating new.")
            faiss_store = FAISS.from_documents([], embeddings)

        # Add new document chunks to the store
        vector_ids = faiss_store.add_documents(chunks)
        print(f"[{datetime.utcnow()}] Added {len(vector_ids)} chunks to FAISS store.")

        # Save updated store
        faiss_store.save_local(VECTOR_DB_DIRECTORY)
        print(f"[{datetime.utcnow()}] FAISS store saved to {VECTOR_DB_DIRECTORY}.")

        # Store chunk metadata in relational DB
        new_chunk_records = []
        for i, chunk in enumerate(chunks):
            vector_id = vector_ids[i] if i < len(vector_ids) else None
            new_chunk_records.append(Chunk(
                id=str(uuid4()),
                document_id=document_id,
                chunk_text=chunk.page_content,
                page_number=chunk.metadata.get("page_number"),
                chunk_index=chunk.metadata.get("chunk_index"),
                vector_id=vector_id
            ))
        print(f"[{datetime.utcnow()}] Prepared {len(new_chunk_records)} chunk records for bulk save.")
        db.bulk_save_objects(new_chunk_records)
        print(f"[{datetime.utcnow()}] Bulk saved chunk records to session.")

        # Update document status to completed
        doc_metadata.status = "completed"
        print(f"[{datetime.utcnow()}] Updating document status to 'completed'.")
        db.commit()
        print(f"[{datetime.utcnow()}] Final DB commit successful.")

        return {"document_id": document_id, "filename": filename, "num_chunks": len(chunks), "status": "completed"}

    except exc.IntegrityError as e:
        db.rollback()
        print(f"[{datetime.utcnow()}] Database IntegrityError: {e}")
        if doc_metadata:
            doc_metadata.status = "failed"
            db.commit() # Attempt to save failure status
        raise ValueError(f"Document with ID {document_id} already exists or similar DB error.") from e
    except Exception as e:
        db.rollback()
        print(f"[{datetime.utcnow()}] Critical Error processing document {filename}: {e}", flush=True)
        if doc_metadata:
            doc_metadata.status = "failed"
            db.commit() # Attempt to save failure status
        raise RuntimeError(f"Failed to process document {filename}: {e}")
    finally:
        if db.is_active: # Check if the session is still active before closing
             db.close()
        print(f"[{datetime.utcnow()}] DB session closed.")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"[{datetime.utcnow()}] Temporary file removed: {temp_file_path}")
