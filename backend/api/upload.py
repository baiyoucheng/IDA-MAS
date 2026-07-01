"""POST /api/upload — file upload and document indexing endpoint."""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.config import settings
from backend.core.document_processor import process_file, SUPPORTED_EXTENSIONS
from backend.core.text_chunker import split_text
from backend.core.vector_store import add_documents
from backend.models.document_models import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """Upload a document (PDF / DOCX / TXT), parse it, chunk it, and index
    it into the vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Read file content
    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大 ({len(content) / 1024 / 1024:.1f} MB)，最大支持 {settings.MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
        )

    # Save to disk with unique name to avoid collisions
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path = upload_dir / safe_name
    save_path.write_bytes(content)

    # Parse the document
    try:
        text = process_file(save_path)
    except Exception as exc:
        logger.error("Document parse error: %s", exc)
        raise HTTPException(status_code=500, detail=f"文档解析失败: {exc}")

    if not text:
        raise HTTPException(status_code=422, detail="文档内容为空，无法提取文本。请确认文件非扫描件且包含可提取的文字。")

    # Chunk & index
    try:
        chunks = split_text(text, doc_name=file.filename)
        chunk_count = add_documents(chunks, doc_name=file.filename)
    except Exception as exc:
        logger.error("Indexing error: %s", exc)
        raise HTTPException(status_code=500, detail=f"文档索引失败: {exc}")

    logger.info("Uploaded '%s' → %d chunks", file.filename, chunk_count)

    return UploadResponse(
        filename=file.filename,
        chunk_count=chunk_count,
        message=f"上传成功，已拆分为 {chunk_count} 个片段并建立索引。",
    )
