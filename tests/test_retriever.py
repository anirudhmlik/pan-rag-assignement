import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.documents import Document as LangchainDocument
from app.services.retriever import retrieve_chunks, get_faiss_vector_store, VECTOR_DB_DIRECTORY
from app.services.ingest import embeddings # Import embeddings to pass to FAISS.from_documents

@pytest.mark.asyncio
async def test_retrieve_chunks_success(mock_faiss_store_in_retriever):
    """
    Tests successful retrieval of chunks from FAISS.
    `mock_faiss_store_in_retriever` fixture already provides a mocked FAISS instance.
    """
    # Configure the mock FAISS instance's similarity_search method
    expected_docs = [
        LangchainDocument(page_content="This is a relevant document chunk 1."),
        LangchainDocument(page_content="This is another relevant document chunk 2.")
    ]
    mock_faiss_store_in_retriever.similarity_search.return_value = expected_docs

    query_text = "test query"
    top_k = 2
    retrieved_chunks = await retrieve_chunks(query_text, top_k)

    # Assertions
    assert retrieved_chunks == expected_docs
    mock_faiss_store_in_retriever.similarity_search.assert_called_once_with(query_text, k=top_k)
    
    # Assert get_faiss_vector_store was called, which internally uses load_local or from_documents
    # No direct assert on mock_faiss_class.load_local.call_args[0][0] is needed here
    # as the fixture already ensures the mocking is in place.
    # The `get_faiss_vector_store` function would internally call load_local or from_documents
    # depending on existence, and the fixture mocks both.

@pytest.mark.asyncio
async def test_retrieve_chunks_file_not_found():
    """
    Tests retrieval when the FAISS index file is not found.
    """
    # Simulate FileNotFoundError when trying to load FAISS index
    with patch('app.services.retriever.FAISS.load_local', side_effect=FileNotFoundError("FAISS index not found")), \
         patch('app.services.retriever.FAISS.from_documents', return_value=MagicMock()) as mock_from_documents: # Mock from_documents if load fails and a new one is created
        
        # Ensure embeddings are available for `from_documents` if it's called
        with patch('app.services.retriever.embeddings', new_callable=MagicMock) as mock_embed:
            mock_embed.embed_documents.return_value = [[0.1]*384]
            mock_embed.embed_query.return_value = [0.1]*384

            query_text = "nonexistent query"
            retrieved_chunks = await retrieve_chunks(query_text)

            assert retrieved_chunks == []
            # Check if load_local was attempted
            assert mock_load_local.called
            # Check if from_documents was called (as a fallback when load_local fails)
            assert mock_from_documents.called


@pytest.mark.asyncio
async def test_retrieve_chunks_llm_error():
    """
    Tests retrieval when an unexpected error occurs during similarity search.
    This test is designed to expect a RuntimeError.
    """
    # Mock FAISS.load_local to return a mock instance
    with patch('app.services.retriever.FAISS.load_local') as mock_load_local:
        mock_faiss_instance = MagicMock()
        mock_load_local.return_value = mock_faiss_instance
        
        # Simulate an exception during similarity search
        mock_faiss_instance.similarity_search.side_effect = Exception("Simulated FAISS search error")

        query_text = "test query"
        top_k = 2
        
        with pytest.raises(RuntimeError) as excinfo:
            await retrieve_chunks(query_text, top_k)
        
        assert "Unexpected error during retrieval: Simulated FAISS search error" in str(excinfo.value)
        mock_faiss_instance.similarity_search.assert_called_once_with(query_text, k=top_k)