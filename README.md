# PanScience Innovations LLM Specialist Assignment - RAG Pipeline

This repository contains the solution for the LLM Specialist Assignment, implementing a Retrieval-Augmented Generation (RAG) pipeline. The system allows users to upload documents, which are then processed, embedded, and stored in a vector database. Users can then ask questions based on the content of these uploaded documents, with responses generated contextually by an LLM. The entire application is containerized using Docker for easy deployment.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup and Installation](#setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Local Setup (Docker Compose)](#local-setup-docker-compose)
  - [Manual Local Setup (for Development)](#manual-local-setup-for-development)
- [API Usage](#api-usage)
  - [Swagger UI](#swagger-ui)
  - [Endpoints](#endpoints)
    - [Upload Documents (`POST /upload/documents`)](#upload-documents-post-uploaddocuments)
    - [Query System (`POST /query/ask`)](#query-system-post-queryask)
    - [View Document Metadata (`GET /documents/metadata`)](#view-document-metadata-get-documentsmetadata)
- [Configuration Details for LLM Providers](#configuration-details-for-llm-providers)
- [Testing Guidelines](#testing-guidelines)
- [Deployment Notes](#deployment-notes)
- [Evaluation Criteria Addressed](#evaluation-criteria-addressed)
- [Future Enhancements](#future-enhancements)

## Features

* [cite_start]**Document Ingestion & Processing**: [cite: 7]
    * [cite_start]Supports uploading PDF and TXT documents (up to 20 documents, max 100MB each). [cite: 8]
    * [cite_start]Automatic chunking of documents into manageable sizes. [cite: 9]
    * [cite_start]Generates text embeddings for document chunks. [cite: 10]
    * [cite_start]Stores chunks and embeddings in a local FAISS vector database. [cite: 10]
    * [cite_start]Stores document metadata (filename, upload status, etc.) in a PostgreSQL database. [cite: 22]
* [cite_start]**Retrieval-Augmented Generation (RAG) Pipeline**: [cite: 11]
    * [cite_start]Accepts user queries. [cite: 12]
    * [cite_start]Retrieves top-K most relevant document chunks based on the query. [cite: 12]
    * [cite_start]Passes retrieved chunks and the query to an LLM API (OpenAI/Gemini) for contextual response generation. [cite: 14]
    * [cite_start]Ensures responses are accurate, concise, and relevant to uploaded documents. [cite: 15]
* [cite_start]**API & Application Architecture**: [cite: 16]
    * [cite_start]Implemented as a REST API using FastAPI. [cite: 17, 18]
    * [cite_start]Exposes endpoints for document upload, system querying, and viewing document metadata. [cite: 19, 20, 21]
* [cite_start]**Deployment & Containerization**: [cite: 23]
    * [cite_start]Provided with a `Dockerfile` and `docker-compose.yml` for easy setup. [cite: 24]
    * [cite_start]Ensures seamless deployment on local machines. [cite: 25]
* [cite_start]**Testing & Documentation**: [cite: 26]
    * [cite_start]Includes unit and integration tests for core functionalities. [cite: 27]
    * [cite_start]Comprehensive `README.md` with setup and usage instructions. [cite: 28]

## Requirements

* Docker and Docker Compose (v1.28+ recommended)
* Python 3.9+ (for local development/testing)

## Setup and Installation

### Prerequisites

Ensure Docker Desktop (or Docker Engine and Docker Compose) is installed and running on your system.

### Local Setup (Docker Compose)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-github-username/pan-rag-assignment.git](https://github.com/your-github-username/pan-rag-assignment.git)
    cd pan-rag-assignment
    ```

2.  **Create `.env` file:**
    Create a file named `.env` in the root directory of the project and populate it with your API keys and configuration:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    GEMINI_API_KEY=your_gemini_api_key_here
    LLM_PROVIDER=openai # Set to 'openai' or 'gemini'
    DATABASE_URL="postgresql+psycopg2://user:password@metadata_db/panscience_rag_db"
    EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
    VECTOR_DB_PATH=/app/vector_db_data/faiss_index # Path inside container for persistent FAISS index
    ```
    *Replace `your_openai_api_key_here` and `your_gemini_api_key_here` with your actual API keys.*

3.  **Build and run the Docker containers:**
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    * Build the `rag_app` Docker image.
    * Start the `rag_app` (FastAPI) service.
    * Start the `metadata_db` (PostgreSQL) service.
    * Create persistent volumes for database data and FAISS index.

4.  **Initialize the Database Schema:**
    You'll need to create the database tables. You can do this by running a command inside the `rag_app` container once:
    ```bash
    docker exec -it <container_id_of_rag_app> python -c "from app.models.metadata import init_db; init_db()"
    ```
    To find `<container_id_of_rag_app>`, run `docker ps`.

5.  **Access the application:**
    The FastAPI application will be accessible at `http://localhost:8000`.

### Manual Local Setup (for Development)

This is useful if you prefer to run the FastAPI app directly without Docker for faster iteration (though DB and Vector DB might still need Docker or manual setup).

1.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set environment variables:**
    Make sure your `.env` file is present in the root directory, and run:
    ```bash
    export $(grep -v '^#' .env | xargs) # On Linux/macOS
    # On Windows, you'll need to set them manually or use a library like `python-dotenv` directly in your script.
    ```
4.  **Start the PostgreSQL database (e.g., via Docker Compose):**
    ```bash
    docker-compose up -d metadata_db
    ```
5.  **Initialize the Database Schema:**
    Run this command from your virtual environment:
    ```bash
    python -c "from app.models.metadata import init_db; init_db()"
    ```
6.  **Run the FastAPI application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

## API Usage

### Swagger UI

Once the application is running, you can access the interactive API documentation (Swagger UI) at:
`http://localhost:8000/docs`

This interface allows you to test all available endpoints directly from your browser.

### Endpoints

#### [cite_start]Upload Documents (`POST /upload/documents`) [cite: 19]

* **Description**: Uploads one or more PDF/TXT documents for processing. [cite_start]Documents will be chunked, embedded, and stored. [cite: 7]
* **Method**: `POST`
* **URL**: `http://localhost:8000/upload/documents`
* **Content-Type**: `multipart/form-data`
* **Form Data**:
    * `files`: Multiple file inputs (select your PDF or TXT documents).
* **Constraints**:
    * [cite_start]Supports up to 20 documents per request. [cite: 8]
    * [cite_start]Each document has a maximum size of approximately 100MB (proxy for 1000 pages). [cite: 8]
* **Example Response**:
    ```json
    {
      "message": "Document upload process initiated for all files.",
      "results": [
        {
          "document_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
          "filename": "my_document.pdf",
          "num_chunks": 15,
          "status": "completed"
        },
        {
          "filename": "another_doc.txt",
          "status": "failed",
          "detail": "Unsupported file type: another_doc.txt"
        }
      ]
    }
    ```

#### [cite_start]Query System (`POST /query/ask`) [cite: 20]

* **Description**: Asks a question against the content of the uploaded documents. [cite_start]The system retrieves relevant chunks and uses an LLM to generate a contextual answer. [cite: 12, 14]
* **Method**: `POST`
* **URL**: `http://localhost:8000/query/ask`
* **Content-Type**: `application/json`
* **Request Body**:
    ```json
    {
      "query": "What is the main topic of the PanScience Innovations document?",
      "top_k": 5
    }
    ```
    * `query` (string, required): The question you want to ask.
    * `top_k` (integer, optional, default: 4): The number of top relevant chunks to retrieve.
* **Example Response**:
    ```json
    {
      "query": "What is the main topic of the PanScience Innovations document?",
      "response": "The PanScience Innovations document outlines an LLM Specialist Assignment focused on building a Retrieval-Augmented Generation (RAG) pipeline."
    }
    ```

#### [cite_start]View Document Metadata (`GET /documents/metadata`) [cite: 21]

* [cite_start]**Description**: Retrieves a list of metadata for all documents that have been uploaded and processed. [cite: 21]
* **Method**: `GET`
* **URL**: `http://localhost:8000/documents/metadata`
* **Query Parameters**:
    * `skip` (integer, optional, default: 0): Number of records to skip for pagination.
    * `limit` (integer, optional, default: 100): Maximum number of records to return.
    * `status_filter` (string, optional): Filter documents by their processing status (e.g., "processing", "completed", "failed").
* **Example Response**:
    ```json
    [
      {
        "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "filename": "report_2023.pdf",
        "uploaded_at": "2024-07-28T10:00:00.000000",
        "num_pages": 10,
        "status": "completed"
      },
      {
        "id": "f5e4d3c2-b1a0-9876-5432-10fedcba9876",
        "filename": "notes.txt",
        "uploaded_at": "2024-07-27T15:30:00.000000",
        "num_pages": null,
        "status": "failed"
      }
    ]
    ```

## Configuration Details for LLM Providers

The application supports different LLM providers through environment variables.

* **`LLM_PROVIDER`**: Set this to `openai` or `gemini` in your `.env` file.
* **`OPENAI_API_KEY`**: If `LLM_PROVIDER` is `openai`, set your OpenAI API key here.
* **`GEMINI_API_KEY`**: If `LLM_PROVIDER` is `gemini`, set your Google Gemini API key here.

**Example for OpenAI:**
**Example for Gemini:**

## Testing Guidelines

[cite_start]Unit and integration tests are provided in the `tests/` directory. [cite: 27]

1.  **Ensure Docker Compose is running (at least the `metadata_db` service if testing locally without app container):**
    ```bash
    docker-compose up -d metadata_db
    ```
2.  **Run tests (from the root of the project):**
    ```bash
    # If running inside the rag_app container:
    docker exec <container_id_of_rag_app> pytest /app/tests

    # If running locally from your virtual environment:
    pytest tests/
    ```
    This will execute all tests defined in the `tests/` directory.

## Deployment Notes

[cite_start]The `docker-compose.yml` provides a setup for local deployment. [cite: 24] For cloud environments (AWS, GCP, Azure), consider the following:

* **Managed Databases**: Replace the `metadata_db` PostgreSQL container with a managed database service (e.g., AWS RDS, Azure SQL Database, Google Cloud SQL) for better scalability, reliability, and maintenance. Update `DATABASE_URL` accordingly.
* **Managed Vector Stores**: For production-grade applications, consider managed vector databases like Pinecone, Weaviate, or ChromaDB Cloud. These offer better scalability and performance than a local FAISS index. If using them, update `app/services/ingest.py` and `app/services/retriever.py` to use their respective clients.
* **Environment Variables**: Securely manage your environment variables (API keys, database credentials) using cloud-native secret management services (e.g., AWS Secrets Manager, Azure Key Vault, Google Secret Manager).
* **Container Orchestration**: Deploy your `rag_app` using container orchestration services like Kubernetes (EKS, GKE, AKS) or serverless container platforms (AWS ECS/Fargate, Azure Container Apps, Google Cloud Run).
* **Persistent Storage**: Ensure persistent storage for your FAISS index (if keeping it file-based) or switch to a managed vector store.

## Evaluation Criteria Addressed

This project aims to address the following evaluation criteria:

* [cite_start]**Efficiency of document retrieval and response generation**: Achieved through chunking, embeddings, vector database similarity search, and direct LLM API integration. [cite: 39]
* [cite_start]**Scalability and performance of the RAG pipeline**: Modular architecture with FastAPI, separate services (DB, LLM), and containerization supports scalability. [cite: 40]
* [cite_start]**Code quality, modularity, and adherence to best practices**: Organized into logical modules (services, routes, models), uses FastAPI best practices, and follows Python coding standards. [cite: 42]
* [cite_start]**Ease of setup and deployment using Docker**: Provided `Dockerfile` and `docker-compose.yml` ensure a straightforward setup process. [cite: 43]
* [cite_start]**Thoroughness of documentation and test coverage**: Comprehensive `README.md` and dedicated test suite for core functionalities. [cite: 44]

## Future Enhancements

* Support for more document types (e.g., DOCX, Markdown, HTML).
* Advanced chunking strategies (e.g., semantic chunking).
* Integration with cloud-native vector databases (Pinecone, Weaviate, Qdrant).
* Asynchronous document ingestion for large files (e.g., using Celery/Redis queues).
* User authentication and authorization.
* More sophisticated error handling and logging.
* UI for easier interaction.
* Metrics and monitoring.
* Fine-tuning of the RAG prompt for specific domains.
* Support for multiple FAISS indexes or named vector stores for multi-document querying contexts.