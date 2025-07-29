#test_ingest.py

import pytest
from unittest.mock import patch, MagicMock
from app.services.ingest import process_document, embeddings, get_faiss_vector_store
from app.models.metadata import SessionLocal, Document, Chunk, init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
# Mock the database engine for testing
@pytest.fixture(scope="module")
def mock_db_session():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    init_db_func = MagicMock() # Mock init_db so it doesn't try to connect to postgres
    init_db_func() # Call it once to ensure tables are created in the mock DB
    Session = sessionmaker(bind=engine)
    SessionLocal.configure(bind=engine) # Configure SessionLocal to use the mock engine

    # Create tables in the in-memory SQLite
    from app.models.metadata import Base
    Base.metadata.create_all(bind=engine)

    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Clean up after tests

@pytest.fixture(autouse=True)
def mock_embeddings():
    with patch('app.services.ingest.HuggingFaceEmbeddings') as mock_hf_embeddings:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]] # Mock embeddings
        mock_hf_embeddings.return_value = mock_instance
        yield mock_instance

@pytest.fixture(autouse=True)
def mock_faiss():
    with patch('app.services.ingest.FAISS') as mock_faiss_class:
        mock_instance = MagicMock()
        mock_instance.add_documents.return_value = ["vec_id_1", "vec_id_2"] # Mock vector IDs
        mock_instance.save_local.return_value = None
        mock_faiss_class.load_local.return_value = mock_instance
        mock_faiss_class.from_texts.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_process_document_success(mock_db_session):
    test_pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n4 0 obj<</Length 11>>stream\nBT /F1 12 Tf 0 0 Td (Hello World) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000054 00000 n\n0000000100 00000 n\n0000000185 00000 n\ntrailer<</Size 5/Root 1 0 R>>startxref\n200\n%%EOF"
    filename = "test_document.pdf"

    with patch('app.services.ingest.PyPDFLoader') as mock_loader_class:
        mock_doc = MagicMock()
        mock_doc.page_content = "This is a test document content."
        mock_doc.metadata = {"page": 1}
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc] # Mock a single page document
        mock_loader_class.return_value = mock_loader_instance

        result = await process_document(test_pdf_content, filename)

        assert result["status"] == "completed"
        assert result["filename"] == filename
        assert "document_id" in result
        assert result["num_chunks"] > 0

        # Verify database entries
        doc = mock_db_session.query(Document).filter_by(id=result["document_id"]).first()
        assert doc is not None
        assert doc.status == "completed"
        assert doc.filename == filename

        chunks = mock_db_session.query(Chunk).filter_by(document_id=result["document_id"]).all()
        assert len(chunks) == result["num_chunks"]
        assert chunks[0].chunk_text == mock_doc.page_content # Check content of the first chunk
        assert chunks[0].vector_id is not None # Ensure vector ID was stored