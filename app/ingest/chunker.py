from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import get_settings
from app.ingest.extractor import ExtractedDocument


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_name: str
    source_path: str
    page_number: int
    chunk_index: int
    char_start: int
    char_end: int
    text: str


def split_text(text: str, chunk_size: int = 900, chunk_overlap: int = 150) -> list[tuple[int, int, str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be zero or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    stripped_text = text.strip()
    if not stripped_text:
        return []

    chunks: list[tuple[int, int, str]] = []
    text_length = len(stripped_text)
    start = 0

    while start < text_length:
        max_end = min(start + chunk_size, text_length)
        end = max_end

        if max_end < text_length:
            whitespace_index = stripped_text.rfind(" ", start, max_end)
            if whitespace_index > start:
                end = whitespace_index

        chunk_text = stripped_text[start:end].strip()
        if chunk_text:
            chunks.append((start, end, chunk_text))

        if end >= text_length:
            break

        next_start = max(0, end - chunk_overlap)
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def chunk_documents(
    documents: list[ExtractedDocument],
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    chunks: list[Chunk] = []

    for document in documents:
        for page in document.pages:
            page_chunks = split_text(
                page.text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            for chunk_index, (char_start, char_end, chunk_text) in enumerate(page_chunks):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.document_id}-p{page.page_number}-c{chunk_index}",
                        document_id=document.document_id,
                        document_name=document.document_name,
                        source_path=document.source_path,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        char_start=char_start,
                        char_end=char_end,
                        text=chunk_text,
                    )
                )

    return chunks


def write_chunk_output(chunks: list[Chunk], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": [asdict(chunk) for chunk in chunks],
        "chunk_count": len(chunks),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def default_output_path() -> Path:
    settings = get_settings()
    return settings.vector_store_dir.parent / "chunks" / "chunks.json"
