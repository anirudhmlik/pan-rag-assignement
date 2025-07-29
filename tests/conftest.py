import pytest
import os
from dotenv import load_dotenv
import httpx
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from app.models.metadata import init_db, SessionLocal, engine, Base
from app.main import app # Import your FastAPI app instance
import logging

logging.basicConfig(level=logging.DEBUG) # Set to DEBUG for more output

# Load environment variables from .env.test for testing
# This should be loaded once at the start of conftest
load_dotenv(dotenv_path="./.env.test")
logging.debug(f"Loaded test environment from {os.path.abspath('./.env.test')}")

# Ensure DATABASE_URL is set for tests
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_db.sqlite")
logging.debug(f"DATABASE_URL in conftest: {TEST_DATABASE_URL}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Sets up a temporary SQLite database for testing.
    """
    # Use a unique in-memory database for each test session
    # Or for file-based, use a distinct file. For simplicity with tests, in-memory is common.
    # We will stick to the default in `metadata.py` which is `sqlite:///./test.db`
    # or override it via DATABASE_URL env var, which we do with `sqlite:///:memory:`
    
    # If using a file-based test db, uncomment these:
    # if database_exists(TEST_DATABASE_URL):
    #     drop_database(TEST_DATABASE_URL)
    # create_database(TEST_DATABASE_URL)
    
    # For in-memory, just ensure `init_db()` is called per test run/session if needed
    # but FastAPI lifespan handles this.

    # Ensure all tables are created before tests run
    # Base.metadata.create_all(bind=engine) # This is handled by FastAPI's lifespan now

    yield
    
    # Clean up after tests if using file-based DB
    # if database_exists(TEST_DATABASE_URL):
    #     drop_database(TEST_DATABASE_URL)
    pass # Cleanup is not strictly needed for in-memory SQLite

@pytest.fixture(scope="function")
def mock_db_session():
    """
    Provides a mock database session for tests to use.
    It uses an in-memory SQLite database for isolation.
    """
    # Create an in-memory SQLite database for the test function
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine) # Create tables for this in-memory DB
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # No need to drop for in-memory, it disappears when session closes.

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def async_client():
    """
    Provides an asynchronous test client for the FastAPI application.
    """
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(autouse=True)
def mock_embeddings_model():
    """
    Mocks the embedding model to prevent actual API calls during tests.
    """
    with patch('app.services.ingest.embeddings') as mock_ingest_embeddings, \
         patch('app.services.retriever.embeddings') as mock_retriever_embeddings:
        # Create a mock for encode method
        mock_encode = MagicMock(return_value=[[0.1] * 384]) # Example embedding
        
        # Assign the mock encode method to both patches
        mock_ingest_embeddings.encode.return_value = [[0.1] * 384] # Simplified mock for encode
        mock_ingest_embeddings.embed_documents.return_value = [[0.1] * 384] # For Langchain Document embedding
        mock_ingest_embeddings.embed_query.return_value = [0.1] * 384 # For Langchain query embedding

        mock_retriever_embeddings.encode.return_value = [[0.1] * 384]
        mock_retriever_embeddings.embed_documents.return_value = [[0.1] * 384]
        mock_retriever_embeddings.embed_query.return_value = [0.1] * 384
        
        # Ensure that the mock is treated as an actual HuggingFaceEmbeddings instance for type checks
        # if the original code uses isinstance checks.
        # This might not be strictly necessary if only method calls are mocked.
        yield # Yield control back to the test

@pytest.fixture(autouse=True)
def mock_llm_model():
    """
    Mocks the LLM model to prevent actual API calls during tests.
    """
    with patch('app.services.llm.ChatOpenAI') as mock_openai_chat:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Mocked LLM response.")
        mock_openai_chat.return_value = mock_instance
        yield

@pytest.fixture(autouse=True)
def mock_faiss_store_in_retriever():
    """
    Mocks FAISS.load_local and FAISS.from_documents in the retriever service.
    """
    with patch('app.services.retriever.FAISS.load_local') as mock_load_local, \
         patch('app.services.retriever.FAISS.from_documents') as mock_from_documents:
        
        mock_faiss_instance = MagicMock()
        mock_faiss_instance.similarity_search.return_value = [
            LangchainDocument(page_content="Mocked chunk 1"),
            LangchainDocument(page_content="Mocked chunk 2")
        ]
        mock_faiss_instance.add_documents.return_value = ["vec_id_1", "vec_id_2"]
        mock_faiss_instance.save_local.return_value = None

        mock_load_local.return_value = mock_faiss_instance
        mock_from_documents.return_value = mock_faiss_instance
        yield mock_faiss_instance # Yield the mock instance itself