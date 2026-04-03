from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import get_settings


WHITESPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class ExtractedPage:
    document_id: str
    document_name: str
    source_path: str
    page_number: int
    text: str


@dataclass(slots=True)
class ExtractedDocument:
    document_id: str
    document_name: str
    source_path: str
    page_count: int
    pages: list[ExtractedPage]


def normalize_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def list_pdf_documents(documents_dir: Path) -> list[Path]:
    return sorted(path for path in documents_dir.glob("*.pdf") if path.is_file())


def extract_document(pdf_path: Path) -> ExtractedDocument:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is not installed. Install project dependencies before running extraction."
        ) from exc

    pages: list[ExtractedPage] = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            page_text = normalize_text(page.get_text("text"))
            if not page_text:
                continue

            pages.append(
                ExtractedPage(
                    document_id=pdf_path.stem,
                    document_name=pdf_path.name,
                    source_path=str(pdf_path),
                    page_number=page_index,
                    text=page_text,
                )
            )

        return ExtractedDocument(
            document_id=pdf_path.stem,
            document_name=pdf_path.name,
            source_path=str(pdf_path),
            page_count=pdf.page_count,
            pages=pages,
        )


def extract_all_documents(documents_dir: Path) -> list[ExtractedDocument]:
    return [extract_document(pdf_path) for pdf_path in list_pdf_documents(documents_dir)]


def serialize_documents(documents: list[ExtractedDocument]) -> list[dict[str, object]]:
    return [asdict(document) for document in documents]


def write_extraction_output(
    documents: list[ExtractedDocument],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "documents": serialize_documents(documents),
        "document_count": len(documents),
        "page_count": sum(len(document.pages) for document in documents),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def default_output_path() -> Path:
    settings = get_settings()
    return settings.vector_store_dir.parent / "extracted" / "documents.json"
