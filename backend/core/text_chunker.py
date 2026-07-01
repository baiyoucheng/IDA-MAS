"""Text chunking — splits long documents into overlapping segments."""

import hashlib
from typing import List

from langchain.schema import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.config import settings


def split_text(
    text: str,
    doc_name: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[LangchainDocument]:
    """Split raw text into overlapping chunks with metadata.

    Args:
        text:        Raw text content.
        doc_name:    Source document filename (for metadata).
        chunk_size:  Max characters per chunk. Defaults to settings.
        chunk_overlap: Overlap between chunks. Defaults to settings.

    Returns:
        List of Langchain Document objects, each with page_content and metadata.
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        keep_separator=True,
    )

    chunks = splitter.split_text(text)

    doc_id = _hash_name(doc_name)
    documents: List[LangchainDocument] = []
    for i, chunk_text in enumerate(chunks):
        documents.append(
            LangchainDocument(
                page_content=chunk_text.strip(),
                metadata={
                    "source": doc_name,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )
        )

    return documents


def _hash_name(name: str) -> str:
    """Short hash for document deduplication."""
    return hashlib.md5(name.encode()).hexdigest()[:8]
