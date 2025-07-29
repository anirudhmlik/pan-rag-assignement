from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.retriever import retrieve_chunks
from app.services.llm import generate_response

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 20  # Number of top relevant chunks to retrieve

class QueryResponse(BaseModel):
    query: str
    response: str

@router.post("/ask", response_model=QueryResponse, summary="Query the RAG system")
async def ask_question(request: QueryRequest):
    """
    Accepts a user query and retrieves relevant document chunks from the vector database.
    These chunks are then passed to the LLM to generate a contextual response.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    try:
        # 1. Retrieve relevant chunks
        retrieved_chunks = await retrieve_chunks(request.query, request.top_k)

        if not retrieved_chunks:
            return QueryResponse(
                query=request.query,
                response="I could not find any relevant information for your query in the uploaded documents."
            )

        # 2. Generate response using LLM
        llm_response = await generate_response(request.query, retrieved_chunks)

        return QueryResponse(
            query=request.query,
            response=llm_response
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your query: {str(e)}"
        )