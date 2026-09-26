"""
Document upload router — equivalent of backend/controllers/documentController.js
+ backend/routes/documentRoutes.js from the Node project.

Accepts PDF file(s) via multipart/form-data, extracts text, chunks it,
and upserts into the vector store. Response shape matches the Node
version exactly so the existing React frontend needs zero changes to
its IngestionPortal.jsx parsing logic.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader
import io

from app.security import get_current_user
from app.services.vectorstore import upsert_documents

logger = logging.getLogger("sentinel.documents")

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Same 1000-char / 200-char-overlap chunking as Node's chunkText()."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if end >= len(text):
            break
    return [c for c in chunks if c.strip()]


@router.post("/upload")
async def upload_documents(
    documents: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user),
):
    """
    POST /api/v1/documents/upload
    multipart/form-data, field name "documents" (matches frontend's FormData key).
    Returns: { status, message, results: [{ filename, chunksGenerated, status }] }
    """
    if not documents:
        raise HTTPException(status_code=400, detail="No files uploaded. Please upload at least one PDF.")

    results = []
    for file in documents:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a PDF. Only PDF files are supported.",
            )

        logger.info(f"[DocumentUpload] Processing file: {file.filename}")
        file_bytes = await file.read()
        text = _extract_pdf_text(file_bytes)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Could not extract any text from the PDF: {file.filename}",
            )

        chunks = _chunk_text(text)
        logger.info(f"[DocumentUpload] Extracted {len(chunks)} chunks from {file.filename}")

        upsert_documents(chunks, file.filename)

        results.append({"filename": file.filename, "chunksGenerated": len(chunks), "status": "success"})

    return {
        "status": "success",
        "message": f"Successfully processed and ingested {len(documents)} document(s).",
        "results": results,
    }
