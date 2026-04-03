import json
import tempfile
import unittest
from pathlib import Path

from app.ingest.extractor import (
    ExtractedDocument,
    ExtractedPage,
    extract_all_documents,
    normalize_text,
    write_extraction_output,
)


class ExtractorTests(unittest.TestCase):
    def test_normalize_text_collapses_whitespace(self) -> None:
        raw_text = "Policy\ttext\n\nwith   uneven   spacing."

        self.assertEqual(normalize_text(raw_text), "Policy text with uneven spacing.")

    def test_write_extraction_output_serializes_metadata(self) -> None:
        document = ExtractedDocument(
            document_id="sample-policy",
            document_name="sample-policy.pdf",
            source_path="documents/sample-policy.pdf",
            page_count=1,
            pages=[
                ExtractedPage(
                    document_id="sample-policy",
                    document_name="sample-policy.pdf",
                    source_path="documents/sample-policy.pdf",
                    page_number=1,
                    text="Sample extracted text",
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "documents.json"

            write_extraction_output([document], output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["document_count"], 1)
        self.assertEqual(payload["page_count"], 1)
        self.assertEqual(payload["documents"][0]["document_name"], "sample-policy.pdf")
        self.assertEqual(payload["documents"][0]["pages"][0]["page_number"], 1)

    def test_extract_all_documents_reads_repo_pdfs(self) -> None:
        documents = extract_all_documents(Path("documents"))

        self.assertEqual(len(documents), 3)
        self.assertTrue(all(document.page_count > 0 for document in documents))
        self.assertTrue(all(document.pages for document in documents))
        self.assertTrue(all(document.pages[0].text for document in documents))
