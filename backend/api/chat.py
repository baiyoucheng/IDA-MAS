"""POST /api/chat — RAG question-answering endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from backend.core.rag_pipeline import query_documents
from backend.models.chat_models import ChatRequest, ChatResponse, SourceCitation

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Answer a question using the RAG pipeline.

    Retrieves relevant document chunks and generates a grounded response
    with source citations.
    """
    try:
        answer, sources_raw = query_documents(req.message)
    except Exception as exc:
        logger.error("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {exc}")

    sources = [
        SourceCitation(
            document=s["document"],
            chunk_preview=s["chunk_preview"],
            chunk_index=s["chunk_index"],
            distance=s["distance"],
        )
        for s in sources_raw
    ]

    return ChatResponse(response=answer, sources=sources)
