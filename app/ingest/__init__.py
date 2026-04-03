"""Ingestion package for loading and indexing policy documents."""

from app.ingest.extractor import ExtractedDocument, ExtractedPage, extract_all_documents

__all__ = ["ExtractedDocument", "ExtractedPage", "extract_all_documents"]
