

🚀 PanScience Innovations – LLM Specialist Assignment (RAG Pipeline)

This repository contains the solution for the PanScience LLM Specialist Assignment — a Retrieval-Augmented Generation (RAG) pipeline. It enables users to upload documents, processes them using embeddings, stores them in a FAISS vector DB, and answers user queries contextually using an LLM (OpenAI or Gemini).

⸻

📑 Table of Contents
	•	✨ Features
	•	🔧 Requirements
	•	⚙️ Setup and Installation
	•	📌 Prerequisites
	•	🐳 Local Setup (Docker)
	•	🧪 Manual Setup (Dev)
	•	🧪 API Usage
	•	🧠 LLM Configuration
	•	✅ Testing
	•	🚀 Deployment Notes
	•	📈 Evaluation Criteria
	•	🔮 Future Enhancements

⸻

✨ Features

<details>
<summary><strong>📄 Document Ingestion & Processing</strong></summary>


	•	Upload PDF/TXT files (max 20, 100MB each).
	•	Automatically chunked into segments.
	•	Embeddings generated via HuggingFace models.
	•	Stored in a FAISS vector database.
	•	Metadata saved in PostgreSQL.

</details>


<details>
<summary><strong>🧠 Retrieval-Augmented Generation (RAG)</strong></summary>


	•	Accepts natural language queries.
	•	Retrieves top-k most relevant chunks.
	•	Sends content + query to an LLM (OpenAI or Gemini).
	•	Returns a contextual, concise answer.

</details>


<details>
<summary><strong>🧱 API Architecture</strong></summary>


	•	Built using FastAPI.
	•	Exposes endpoints for:
	•	Document Upload
	•	Query Execution
	•	Metadata Retrieval
	•	Query History

</details>


<details>
<summary><strong>📦 Containerized & Tested</strong></summary>


	•	Docker & Docker Compose ready.
	•	Persistent volumes for DB + FAISS.
	•	Unit & integration test script included.

</details>



⸻

🔧 Requirements
	•	Docker & Docker Compose (v1.28+)
	•	Python 3.9+ (for manual/local dev)

⸻

⚙️ Setup and Installation

📌 Prerequisites

Install Docker Desktop or Docker Engine + Docker Compose on your system.

⸻

🐳 Local Setup (Docker)

git clone https://github.com/your-github-username/pan-rag-assignment.git
cd pan-rag-assignment

Create a .env file:

OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
LLM_PROVIDER=gemini
DATABASE_URL=postgresql+psycopg2://user:password@metadata_db/panscience_rag_db
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB_DIRECTORY=/app/vector_db_data/faiss_index

Then build and start services:

docker-compose up --build -d

The DB tables (documents, chunks, query_logs) are initialized automatically on first run.

Open the API docs:
📍 http://localhost:8000/docs

⸻

🧪 Manual Setup (Dev)

Useful for debugging without Docker.

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)

Start DB only:

docker-compose up -d metadata_db

Create DB tables:

python -c "from app.models.metadata import Base, engine; Base.metadata.create_all(bind=engine)"

Run the app:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


⸻

📡 API Usage

🧭 Swagger UI

http://localhost:8000/docs

⸻

📤 POST /upload/documents

Upload multiple PDF/TXT files (max: 20 per request, ~100MB each).

Request: multipart/form-data

files: [file1.pdf, file2.txt]

Example Response:

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


⸻

❓ POST /query/ask

Request:

{
  "query": "What is this document about?",
  "top_k": 4
}

Response:

{
  "query": "What is this document about?",
  "response": "The uploaded document is a resume focused on machine learning and AI development."
}


⸻

📄 GET /documents/metadata

Fetch metadata for uploaded documents.

Query params (optional):
	•	skip
	•	limit
	•	status_filter

⸻

📚 GET /query/history

Returns recent queries and their generated responses.

⸻

🔐 LLM Configuration

LLM_PROVIDER=gemini  # or openai
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_openai_key_here


⸻

✅ Testing

<details>
<summary><strong>🧪 Run Tests Inside Docker (Recommended)</strong></summary>


	1.	Ensure Docker is up:

docker-compose up --build -d


	2.	Add a test document:

docker cp test_document.pdf pan-rag-assignement-rag_app-1:/app/test_document.pdf


	3.	Run test:

docker exec -it pan-rag-assignement-rag_app-1 bash
python -m app.test_full_pipeline



✅ Tests document ingestion, FAISS indexing, retrieval, and LLM response.

</details>


<details>
<summary><strong>⚙️ Run Tests Locally (For Devs)</strong></summary>


docker-compose up -d metadata_db
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
python app/test_full_pipeline.py

</details>



⸻

🚀 Deployment Notes
	•	✅ Use RDS / Cloud SQL for production-grade Postgres.
	•	✅ Use Pinecone / Weaviate / Qdrant for scalable vector stores.
	•	✅ Secure env vars using AWS Secrets Manager, GCP Secret Manager, or Docker Swarm/Kubernetes secrets.
	•	✅ Deploy with ECS/Fargate, GKE, or Cloud Run for scalability.

⸻

📈 Evaluation Criteria Addressed
	•	✅ Efficient vector retrieval + LLM response
	•	✅ Modular, scalable architecture (FastAPI + Docker)
	•	✅ Clean code, organized structure
	•	✅ Clear documentation and tests

⸻

🔮 Future Enhancements
	•	DOCX/Markdown support
	•	Semantic chunking
	•	Background ingestion (Celery/Redis)
	•	Auth layer (JWT/OAuth)
	•	Web UI / Streamlit
	•	Metrics + monitoring
	•	Multi-index support (per-user or per-project)

⸻

🧾 1. GitHub Wiki Starter Structure (Optional but Great for Teams)

You can create a GitHub Wiki with the following structure:

🗂 Wiki Structure (Markdown files)
	•	Home.md
Brief intro, architecture diagram, link to README
	•	API.md
Detailed usage of endpoints, with curl/Postman examples
	•	LLM_Configuration.md
Switching between OpenAI/Gemini, setting up .env
	•	Testing.md
Guide on using test_full_pipeline.py, pytest, or Docker tests
	•	Deployment.md
Docker Compose, cloud deployment notes

✅ How to Add:
	1.	On GitHub repo page → click the “Wiki” tab.
	2.	Start with Home and link other pages.
	3.	You can copy most of the content from your README sections to populate it.

Want me to generate the .md files for you? Just say yes.

⸻

📘 2. mkdocs.yml + Docs Structure for Static Site Docs (like https://docs.streamlit.io)

mkdocs.yml (basic)

site_name: PanScience RAG Pipeline
theme:
  name: material
nav:
  - Home: index.md
  - Setup: setup.md
  - API Usage: api.md
  - Testing: testing.md
  - Deployment: deployment.md
  - LLM Config: llm.md
  - Future Enhancements: future.md

Folder structure:

/docs
  ├─ index.md
  ├─ setup.md
  ├─ api.md
  ├─ testing.md
  ├─ deployment.md
  ├─ llm.md
  ├─ future.md

Setup:

pip install mkdocs mkdocs-material
mkdocs serve

Want me to generate all those .md files too? Just say yes.

⸻

🔗 3. Postman Environment (clickable import)

You already have the collection, now here’s a simple environment you can import to auto-fill the base URL and LLM provider:

📁 File: PanScience_RAG_Environment.postman_environment.json

{
  "id": "d9b92e42-fd44-41b1-bfa2-baaa2f1812ab",
  "name": "PanScience RAG Environment",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "llm_provider",
      "value": "gemini",
      "enabled": true
    }
  ],
  "_postman_variable_scope": "environment",
  "_postman_exported_at": "2025-07-30T10:00:00.000Z",
  "_postman_exported_using": "Postman/10.23.0"
}

✅ How to Use
	1.	Open Postman
	2.	Go to Environments → Import
	3.	Select the above JSON file
	4.	Use {{base_url}}/upload/documents in your requests

⸻

