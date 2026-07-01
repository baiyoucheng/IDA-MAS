"""Document parser — extracts raw text from PDF, DOCX, and TXT files."""

import logging
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def process_file(file_path: Path) -> Optional[str]:
    """Extract text content from a file. Returns None on failure.

    Dispatch is by file extension; unknown types return None.
    """
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return _process_pdf(file_path)
    elif ext == ".docx":
        return _process_docx(file_path)
    elif ext == ".txt":
        return _process_txt(file_path)
    else:
        logger.warning("Unsupported extension: %s", ext)
        return None


# ---------------------------------------------------------------------------
# Per-format parsers
# ---------------------------------------------------------------------------


def _process_pdf(path: Path) -> Optional[str]:
    try:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        content = "\n".join(pages)
        return _clean(content)
    except Exception as exc:
        logger.error("PDF parse error (%s): %s", path.name, exc)
        return None


def _process_docx(path: Path) -> Optional[str]:
    try:
        from docx import Document  # lazy import
        doc = Document(str(path))
        paragraphs: list[str] = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        content = "\n".join(paragraphs)
        return _clean(content)
    except Exception as exc:
        logger.error("DOCX parse error (%s): %s", path.name, exc)
        return None


def _process_txt(path: Path) -> Optional[str]:
    try:
        content = path.read_text(encoding="utf-8")
        return _clean(content)
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="gbk")
            return _clean(content)
        except Exception as exc:
            logger.error("TXT parse error (%s): %s", path.name, exc)
            return None
    except Exception as exc:
        logger.error("TXT parse error (%s): %s", path.name, exc)
        return None


def _clean(text: str) -> str:
    """Light cleanup: collapse whitespace lines, keep structure."""
    lines = [ln.strip() for ln in text.splitlines()]
    # Remove multiple consecutive blank lines
    cleaned: list[str] = []
    for ln in lines:
        if not ln and cleaned and not cleaned[-1]:
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()
