#test_query.py

import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import MagicMock, AsyncMock, patch

# Fixture to provide an async client for testing FastAPI app
@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_ask_question_success(async_client):
    # Mock the retriever and LLM services
    with patch('app.services.retriever.retrieve_chunks', new_callable=AsyncMock) as mock_retrieve_chunks, \
         patch('app.services.llm.generate_response', new_callable=AsyncMock) as mock_generate_response:

        # Configure mock return values
        mock_chunks = [
            MagicMock(page_content="The capital of France is Paris."),
            MagicMock(page_content="Eiffel Tower is in Paris.")
        ]
        mock_retrieve_chunks.return_value = mock_chunks
        mock_generate_response.return_value = "Paris is the capital of France and home to the Eiffel Tower."

        query_payload = {"query": "What is the capital of France?"}
        response = await async_client.post("/query/ask", json=query_payload)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["query"] == "What is the capital of France?"
        assert response_data["response"] == "Paris is the capital of France and home to the Eiffel Tower."

        mock_retrieve_chunks.assert_called_once_with(query_payload["query"], 4)
        mock_generate_response.assert_called_once_with(query_payload["query"], mock_chunks)

@pytest.mark.asyncio
async def test_ask_question_no_query(async_client):
    query_payload = {"query": ""}
    response = await async_client.post("/query/ask", json=query_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Query cannot be empty."

@pytest.mark.asyncio
async def test_ask_question_no_relevant_chunks(async_client):
    with patch('app.services.retriever.retrieve_chunks', new_callable=AsyncMock) as mock_retrieve_chunks:
        mock_retrieve_chunks.return_value = [] # No chunks found

        query_payload = {"query": "Non-existent topic?"}
        response = await async_client.post("/query/ask", json=query_payload)

        assert response.status_code == 200 # Still 200, as it's a valid query, just no info
        response_data = response.json()
        assert response_data["response"] == "I could not find any relevant information for your query in the uploaded documents."