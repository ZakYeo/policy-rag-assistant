from __future__ import annotations

import argparse
from pathlib import Path

from app.config import get_settings
from app.ingest.chunker import chunk_documents
from app.ingest.extractor import extract_all_documents
from app.ingest.indexer import build_default_indexer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract, chunk, embed, and index local policy PDFs into Chroma.",
    )
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=None,
        help="Directory containing source PDF files. Defaults to DOCUMENTS_DIR.",
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
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the target collection before indexing.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    documents_dir = args.documents_dir or settings.documents_dir

    documents = extract_all_documents(documents_dir)
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    indexer = build_default_indexer()
    if args.reset:
        indexer.reset()
    indexed_count = indexer.upsert_chunks(chunks)

    print(
        "Indexed "
        f"{indexed_count} chunks from {len(documents)} documents into "
        f"{settings.vector_store_collection} at {settings.vector_store_dir}"
    )


if __name__ == "__main__":
    main()
