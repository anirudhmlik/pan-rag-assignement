# app/main.py

from fastapi import FastAPI, HTTPException, status
from .routes import upload, query, documents
import os
from datetime import datetime

# --- Crucial Imports for the /query/ask endpoint ---
from app.routes.query import QueryRequest, QueryResponse
from app.services.retriever import get_faiss_vector_store
from app.services.llm import llm # Import the global llm instance
# --- NEW: Imports for database schema creation ---
from app.models.metadata import Base, engine # Import Base and engine
# --- End NEW Imports ---


# Initialize FastAPI app
app = FastAPI(
    title="PanScience RAG Pipeline",
    description="API for Document Ingestion and Retrieval-Augmented Generation",
    version="1.0.0",
)

# Include routers
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

@app.get("/")
async def root():
    """
    Root endpoint for the RAG API.
    """
    return {"message": "Welcome to the PanScience RAG API!"}

# Optional: Add an event handler to load environment variables for local runs
# In a Docker environment, these are usually handled by docker-compose's env_file
@app.on_event("startup")
async def startup_event():
    # Load environment variables (if .env exists)
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded from .env file.")

    # --- NEW: Create database tables on startup ---
    print(f"[{datetime.utcnow()}] Attempting to create database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[{datetime.utcnow()}] Database tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"[{datetime.utcnow()}] ERROR: Failed to create database tables: {e}", flush=True)
        # It's critical to raise an exception here if table creation fails,
        # as the app cannot function without the database.
        raise RuntimeError(f"Database table creation failed: {e}")
    # --- End NEW ---


# The /query/ask endpoint is placed here for debugging purposes as discussed.
# For better project structure, it should ideally be in app/routes/query.py
# If you have this endpoint already defined in app/routes/query.py,
# this definition here in main.py will override it.
@app.post("/query/ask", response_model=QueryResponse)
async def ask_query(query_request: QueryRequest):
    """
    Accepts a user query and retrieves relevant document chunks from the vector database.
    These chunks are then passed to the LLM to generate a contextual response.
    """
    if not query_request.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

    current_query = query_request.query
    top_k = query_request.top_k

    # Ensure LLM instance is initialized
    if llm is None:
        print(f"[{datetime.utcnow()}] LLM instance is None. This indicates an issue during LLM initialization in app/services/llm.py (e.g., missing/invalid API key, network issue).")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM service not initialized. Please check server logs for details.")

    print(f"[{datetime.utcnow()}] Received query: '{current_query}' with top_k: {top_k}")

    try:
        # Retrieve chunks from the vector store
        faiss_store = get_faiss_vector_store()
        print(f"[{datetime.utcnow()}] FAISS store loaded for query.")

        # Perform similarity search to get relevant documents
        retrieved_docs = faiss_store.similarity_search(current_query, k=top_k)
        print(f"[{datetime.utcnow()}] Retrieved {len(retrieved_docs)} documents from FAISS.")

        # Log the content of the retrieved documents for debugging
        if not retrieved_docs:
            print(f"[{datetime.utcnow()}] No relevant documents retrieved for query: '{current_query}'")
            return {"query": current_query, "response": "I could not find any relevant information for your query in the uploaded documents."}

        for i, doc in enumerate(retrieved_docs):
            print(f"[{datetime.utcnow()}] Retrieved Document {i+1} (Source: {doc.metadata.get('source', 'N/A')}, Page: {doc.metadata.get('page_number', 'N/A')}, Chunk Index: {doc.metadata.get('chunk_index', 'N/A')}):")
            print(f"Chunk content: {doc.page_content[:500]}...") # Print first 500 chars for better visibility

        # Prepare context for LLM from the retrieved chunks
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        print(f"[{datetime.utcnow()}] Context prepared for LLM with {len(context)} characters.")

        # Define the RAG prompt template
        prompt_template = f"""
        Use the following pieces of context to answer the user's question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:
        {context}

        Question: {current_query}

        Answer:
        """
        print(f"[{datetime.utcnow()}] Sending prompt to LLM. Prompt length: {len(prompt_template)} characters.")

        # Invoke the LLM to generate the response
        try:
            response = llm.invoke(prompt_template)
            print(f"[{datetime.utcnow()}] LLM response received. Response length: {len(response.content)} characters.")
            return {"query": current_query, "response": response.content}
        except Exception as llm_error:
            print(f"[{datetime.utcnow()}] ERROR: LLM invocation failed: {llm_error}", flush=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"LLM API error: {str(llm_error)}")

    except FileNotFoundError as e:
        print(f"[{datetime.utcnow()}] FileNotFoundError during query: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vector database not found. Please ingest documents first: {str(e)}")
    except ValueError as e:
        print(f"[{datetime.utcnow()}] ValueError during query: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"[{datetime.utcnow()}] General Error during query processing: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while processing the query: {str(e)}")