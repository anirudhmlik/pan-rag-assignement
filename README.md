# 🚀 PanScience Innovations – LLM Specialist Assignment (RAG Pipeline)

This repository contains the solution for the PanScience LLM Specialist Assignment — a Retrieval-Augmented Generation (RAG) pipeline. It enables users to upload documents, processes them using embeddings, stores them in a FAISS vector DB, and answers user queries contextually using an LLM (OpenAI or Gemini).

---

## 📁 Table of Contents

* [✨ Features](#-features)
* [⚙️ Setup and Installation](#️-setup-and-installation)

  * [📌 Prerequisites](#-prerequisites)
  * [🐳 Local Setup (Docker)](#-local-setup-docker)
  * [🧲 Manual Setup (Dev)](#-manual-setup-dev)
* [🥪 API Usage](#-api-usage)
* [🧠 LLM Configuration](#-llm-configuration)
* [✅ Testing](#-testing)
* [🚀 Deployment Notes](#-deployment-notes)
* [📈 Evaluation Criteria](#-evaluation-criteria)
* [🔮 Future Enhancements](#-future-enhancements)

---

## ✨ Features

* Upload PDF/TXT files (max 20, 100MB each).
* Automatically chunked into segments.
* Embeddings generated via HuggingFace models.
* Stored in a FAISS vector database.
* Metadata saved in PostgreSQL.

- Accepts natural language queries.
- Retrieves top-k most relevant chunks.
- Sends content + query to an LLM (OpenAI or Gemini).
- Returns a contextual, concise answer.

* Built using FastAPI.
* Exposes endpoints for:

  * Document Upload
  * Query Execution
  * Metadata Retrieval
  * Query History

- Docker & Docker Compose ready.
- Persistent volumes for DB + FAISS.
- Unit & integration test script included.

---

## ⚙️ Setup and Installation

### 📌 Prerequisites

Install Docker Desktop or Docker Engine + Docker Compose on your system.

---

### 🐳 Local Setup (Docker)

```bash
git clone https://github.com/your-github-username/pan-rag-assignment.git
cd pan-rag-assignment
```

Create a `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
LLM_PROVIDER=gemini
DATABASE_URL=postgresql+psycopg2://user:password@metadata_db/panscience_rag_db
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB_DIRECTORY=/app/vector_db_data/faiss_index
```

Then build and start services:

```bash
docker-compose up --build -d
```

The DB tables (`documents`, `chunks`, `query_logs`) are initialized automatically on first run.

Open the API docs:
📍 [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 🧲 Manual Setup (Dev)

Useful for debugging without Docker.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
```

Start DB only:

```bash
docker-compose up -d metadata_db
```

Create DB tables:

```bash
python -c "from app.models.metadata import Base, engine; Base.metadata.create_all(bind=engine)"
```

Run the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🛰 API Usage

### 🧽 Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

---

### 📤 `POST /upload/documents`

Upload multiple PDF/TXT files (max: 20 per request, \~100MB each).

**Request:** `multipart/form-data`

```bash
files: [file1.pdf, file2.txt]
```

**Example Response:**

```json
{
  "message": "Document upload process initiated for all files.",
  "results": [
    {
      "document_id": "abc123",
      "filename": "my_resume.pdf",
      "num_chunks": 12,
      "status": "completed"
    }
  ]
}
```

---

### ❓ `POST /query/ask`

**Request:**

```json
{
  "query": "What is this document about?",
  "top_k": 4
}
```

**Response:**

```json
{
  "query": "What is this document about?",
  "response": "The uploaded document is a resume focused on machine learning and AI development."
}
```

---

### 📄 `GET /documents/metadata`

Fetch metadata for uploaded documents.

**Query params (optional):**

* `skip`
* `limit`
* `status_filter`

---

### 📚 `GET /query/history`

Returns recent queries and their generated responses.

---

## 🔐 LLM Configuration

```dotenv
LLM_PROVIDER=gemini  # or openai
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_openai_key_here
```

---

## 🖥️ Streamlit Interface (Optional UI)

```bash
# Step 1: Ensure Docker container is running
docker-compose up --build -d

# Step 2: Access the Streamlit app inside the container
docker exec -it pan-rag-assignement-rag_app-1 streamlit run streamlit_app.py --server.port 8501

# Step 3: Open your browser
# Navigate to the following URL:
http://localhost:8501
```

The Streamlit interface allows:

* Uploading and querying documents interactively
* Switching between OpenAI and Gemini providers
* Viewing document context alongside answers

---

## ✅ Testing

1. Ensure Docker is up:

   ```bash
   docker-compose up --build -d
   ```

2. Add a test document:

   ```bash
   docker cp test_document.pdf pan-rag-assignement-rag_app-1:/app/test_document.pdf
   ```

3. Run test:

   ```bash
   docker exec -it pan-rag-assignement-rag_app-1 bash
   python -m app.test_full_pipeline
   ```

📅 Tests document ingestion, FAISS indexing, retrieval, and LLM response.

```bash
docker-compose up -d metadata_db
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
python app/test_full_pipeline.py
```

---

## 🚀 Deployment Notes

* ✅ Use **RDS / Cloud SQL** for production-grade Postgres.
* ✅ Use **Pinecone / Weaviate / Qdrant** for scalable vector stores.
* ✅ Secure env vars using AWS Secrets Manager, GCP Secret Manager, or Docker Swarm/Kubernetes secrets.
* ✅ Deploy with ECS/Fargate, GKE, or Cloud Run for scalability.

---

## 📈 Evaluation Criteria Addressed

* ✅ Efficient vector retrieval + LLM response
* ✅ Modular, scalable architecture (FastAPI + Docker)
* ✅ Clean code, organized structure
* ✅ Clear documentation and tests

---

## 🔮 Future Enhancements

* DOCX/Markdown support
* Semantic chunking
* Background ingestion (Celery/Redis)
* Auth layer (JWT/OAuth)
* Web UI / Streamlit
* Metrics + monitoring
* Multi-index support (per-user or per-project)

---

This project includes:

* ✅ A [GitHub Wiki](https://github.com/your-github-username/pan-rag-assignment/wiki) with structured guides
* ✅ A `docs/` folder for generating a documentation site via [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material/)
* ✅ A Postman collection and environment for testing API endpoints
* ✅ A Streamlit-based UI for real-time document querying, upload, and LLM responses
