from __future__ import annotations

import argparse
from pathlib import Path

from app.config import get_settings
from app.ingest.extractor import (
    default_output_path,
    extract_all_documents,
    write_extraction_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text and page metadata from local policy PDFs.",
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
        help="Path for extracted JSON output. Defaults to data/extracted/documents.json.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    documents_dir = args.documents_dir or settings.documents_dir
    output_path = args.output or default_output_path()

    extracted_documents = extract_all_documents(documents_dir)
    written_path = write_extraction_output(extracted_documents, output_path)
    page_count = sum(len(document.pages) for document in extracted_documents)

    print(
        f"Extracted {len(extracted_documents)} documents and {page_count} pages to {written_path}"
    )


if __name__ == "__main__":
    main()
