"""Utilities for extracting text from uploaded documents in supported formats."""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from docx import Document as DocxDocument
from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_DOCUMENT_EXTENSIONS: Tuple[str, ...] = (
    ".csv",
    ".docx",
    ".md",
    ".pdf",
    ".txt",
    ".xls",
    ".xlsx",
)


class DocumentParseError(RuntimeError):
    """Raised when a document cannot be parsed into text."""


def _normalize_text(chunks: Iterable[str]) -> str:
    return "\n".join(part.strip() for part in chunks if part and part.strip())


def _parse_pdf(path: Path) -> Tuple[str, Dict[str, Any]]:
    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        texts.append(extracted)
    metadata = {"page_count": len(reader.pages)}
    return _normalize_text(texts), metadata


def _parse_docx(path: Path) -> Tuple[str, Dict[str, Any]]:
    document = DocxDocument(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    metadata = {"paragraph_count": len(paragraphs)}
    return _normalize_text(paragraphs), metadata


def _parse_text_file(path: Path) -> Tuple[str, Dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text.strip(), {"encoding": "utf-8"}


def _parse_markdown(path: Path) -> Tuple[str, Dict[str, Any]]:
    return _parse_text_file(path)


def _parse_csv(path: Path) -> Tuple[str, Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="ignore") as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)
    text_rows = [", ".join(row) for row in rows]
    return _normalize_text(text_rows), {"row_count": len(rows)}


def _parse_excel(path: Path) -> Tuple[str, Dict[str, Any]]:
    try:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    except ValueError:
        # Older XLS files sometimes need engine="xlrd"
        sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine="xlrd")
    rendered_sheets: List[str] = []
    sheet_meta: Dict[str, Any] = {"sheet_names": list(sheets.keys())}
    for sheet_name, frame in sheets.items():
        sheet_buffer = io.StringIO()
        frame.fillna("").to_csv(sheet_buffer, index=False)
        rendered_sheets.append(f"Sheet: {sheet_name}\n{sheet_buffer.getvalue()}")
    return _normalize_text(rendered_sheets), sheet_meta


_PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".txt": _parse_text_file,
    ".md": _parse_markdown,
    ".csv": _parse_csv,
    ".xls": _parse_excel,
    ".xlsx": _parse_excel,
}


def parse_document_file(path: str) -> Tuple[str, Dict[str, Any]]:
    """Parse a document on disk into plain text plus supplemental metadata."""
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise DocumentParseError(f"Document path does not exist: {path}")

    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise DocumentParseError(f"Unsupported document extension: {extension}")

    parser = _PARSERS.get(extension)
    if not parser:
        raise DocumentParseError(f"No parser registered for extension: {extension}")

    text, metadata = parser(file_path)
    if not text.strip():
        raise DocumentParseError("Parsed document is empty after extraction")

    # Truncate overly verbose metadata while preserving structure
    if metadata:
        for key, value in list(metadata.items()):
            if isinstance(value, list) and len(value) > 50:
                metadata[key] = value[:50] + ["…"]
            if isinstance(value, dict):
                metadata[key] = json.loads(json.dumps(value))

    return text, metadata