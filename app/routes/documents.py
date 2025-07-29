#/app/routes/documents

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.models.metadata import SessionLocal, Document, DocumentMetadata
from sqlalchemy.orm import Session
from sqlalchemy import desc

router = APIRouter()

@router.get("/metadata", response_model=List[DocumentMetadata], summary="View processed document metadata")
async def get_document_metadata(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None
):
    """
    Retrieves metadata for all processed documents stored in the system.
    Allows for pagination and filtering by processing status.
    """
    db: Session = SessionLocal()
    try:
        query = db.query(Document)
        if status_filter:
            query = query.filter(Document.status == status_filter)

        documents = query.order_by(desc(Document.uploaded_at)).offset(skip).limit(limit).all()
        return [DocumentMetadata.model_validate(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching document metadata: {str(e)}"
        )
    finally:
        db.close()