from __future__ import annotations

import argparse
from pathlib import Path

from app.config import get_settings
from app.ingest.chunker import chunk_documents, default_output_path, write_chunk_output
from app.ingest.extractor import extract_all_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract and chunk local policy PDFs with page-level metadata.",
    )
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=None,
        help="Directory containing source PDF files. Defaults to DOCUMENTS_DIR.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for chunked JSON output. Defaults to data/chunks/chunks.json.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=900,
        help="Maximum characters per chunk before overlap is applied.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Character overlap between consecutive chunks.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    documents_dir = args.documents_dir or settings.documents_dir
    output_path = args.output or default_output_path()

    documents = extract_all_documents(documents_dir)
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    written_path = write_chunk_output(chunks, output_path)

    print(f"Chunked {len(documents)} documents into {len(chunks)} chunks at {written_path}")


if __name__ == "__main__":
    main()
