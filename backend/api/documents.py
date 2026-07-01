"""GET /api/documents — list indexed documents.
DELETE /api/documents/{name} — remove a document.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.core.vector_store import list_documents, delete_document
from backend.models.document_models import (
    DeleteResponse,
    DocumentListResponse,
    DocumentSummary,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents() -> DocumentListResponse:
    """List all indexed documents and their chunk counts."""
    docs = list_documents()
    summaries = [
        DocumentSummary(
            name=d["name"],
            doc_id=d["doc_id"],
            chunk_count=d["chunk_count"],
            last_indexed=d.get("last_indexed", ""),
        )
        for d in docs
    ]
    return DocumentListResponse(documents=summaries, total=len(summaries))


@router.delete("/documents/{name:path}", response_model=DeleteResponse)
async def remove_document(name: str) -> DeleteResponse:
    """Remove a document and all its chunks from the vector store."""
    deleted = delete_document(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"文档 '{name}' 不存在或已删除")
    return DeleteResponse(filename=name, message=f"文档 '{name}' 及其 {name} 个片段已删除")
