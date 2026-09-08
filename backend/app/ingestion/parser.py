import hashlib
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

from app.ingestion.sanitizer import sanitize_text


@dataclass
class Chunk:
    document_id: str
    page_number: int
    chunk_type: str  # 'table' | 'paragraph'
    raw_text: str
    table_matrix: Optional[List[List[str]]] = None
    chunk_index: int = 0

    def hash(self) -> str:
        return hashlib.sha256(self.raw_text.encode()).hexdigest()


def extract_document(pdf_path: Path, document_id: str) -> List[Chunk]:
    """Extract all text chunks from a PDF. Uses pdfplumber for tables, PyMuPDF for prose."""
    chunks: List[Chunk] = []
    chunk_idx = 0
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                table_bboxes = []

                # Extract tables with coordinate awareness
                tables = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
                if not tables:
                    tables = page.extract_tables()

                for table in (tables or []):
                    if not table or len(table) < 2:
                        continue
                    rows = [[str(cell or "").strip() for cell in row] for row in table if row]
                    table_text = _table_to_text(rows)
                    sanitized = sanitize_text(table_text)
                    if sanitized.strip():
                        chunks.append(Chunk(
                            document_id=document_id,
                            page_number=page_num,
                            chunk_type="table",
                            raw_text=sanitized,
                            table_matrix=rows,
                            chunk_index=chunk_idx,
                        ))
                        chunk_idx += 1

                # Extract prose text
                text = page.extract_text() or ""
                if text.strip():
                    sanitized = sanitize_text(text)
                    for sub in _split_into_chunks(sanitized, max_words=500, overlap=80):
                        if sub.strip():
                            chunks.append(Chunk(
                                document_id=document_id,
                                page_number=page_num,
                                chunk_type="paragraph",
                                raw_text=sub,
                                chunk_index=chunk_idx,
                            ))
                            chunk_idx += 1

    except Exception:
        # Fallback: PyMuPDF
        chunks = _extract_with_pymupdf(pdf_path, document_id)

    return chunks


def get_page_count(pdf_path: Path) -> int:
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            return len(pdf.pages)
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        return 0


def _table_to_text(rows: List[List[str]]) -> str:
    lines = []
    if rows:
        lines.append(" | ".join(rows[0]))
        lines.append("-" * 60)
        for row in rows[1:]:
            lines.append(" | ".join(row))
    return "\n".join(lines)


def _split_into_chunks(text: str, max_words: int = 500, overlap: int = 80) -> List[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += max_words - overlap
    return chunks


def _extract_with_pymupdf(pdf_path: Path, document_id: str) -> List[Chunk]:
    chunks = []
    chunk_idx = 0
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                sanitized = sanitize_text(text)
                for sub in _split_into_chunks(sanitized):
                    if sub.strip():
                        chunks.append(Chunk(
                            document_id=document_id,
                            page_number=page_num + 1,
                            chunk_type="paragraph",
                            raw_text=sub,
                            chunk_index=chunk_idx,
                        ))
                        chunk_idx += 1
        doc.close()
    except Exception:
        pass
    return chunks
