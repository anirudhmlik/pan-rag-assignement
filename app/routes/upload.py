#/app/routes/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
from app.services.ingest import process_document
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post("/documents", response_model=dict, summary="Upload documents for RAG processing")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Uploads multiple documents (PDF, TXT) for ingestion into the RAG pipeline.
    Documents will be chunked, embedded, and stored in the vector database,
    with metadata saved in the relational database.
    [cite_start]Supports up to 20 documents. [cite: 8]
    """
    if not (1 <= len(files) <= 20):  # [cite: 8]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can upload between 1 and 20 documents at a time."
        )

    results = []
    for file in files:
        try:
            # Basic validation: check file type and size
            if not file.filename.endswith((".pdf", ".txt")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.filename}. Only PDF and TXT are allowed."
                )

            # Max file size 1000 pages, roughly equivalent to 10MB per page for simple text, but could vary.
            # A more robust check might involve actual page counting after loading.
            # For simplicity, a general file size limit is used here.
            # [cite_start]1000 pages is a very large document, 100MB is a reasonable proxy for a single PDF. [cite: 8]
            MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024 # 100 MB per file, adjusted from 1000 pages for a practical limit
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File '{file.filename}' exceeds the maximum size of {MAX_FILE_SIZE_BYTES / (1024*1024):.1f} MB."
                )

            process_result = await process_document(file_content, file.filename)
            results.append(process_result)
        except HTTPException as e:
            results.append({"filename": file.filename, "status": "failed", "detail": e.detail})
        except IntegrityError:
            results.append({"filename": file.filename, "status": "failed", "detail": "Document with this ID already exists or a database integrity error occurred."})
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "detail": f"An unexpected error occurred: {str(e)}"})

    return {"message": "Document upload process initiated for all files.", "results": results}