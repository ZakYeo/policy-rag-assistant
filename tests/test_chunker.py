import json
import tempfile
import unittest
from pathlib import Path

from app.ingest.chunker import chunk_documents, split_text, write_chunk_output
from app.ingest.extractor import extract_all_documents


class ChunkerTests(unittest.TestCase):
    def test_split_text_creates_overlapping_chunks(self) -> None:
        text = " ".join(f"word{i}" for i in range(250))

        chunks = split_text(text, chunk_size=120, chunk_overlap=20)

        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(max(len(chunk[2]) for chunk in chunks), 120)
        self.assertLess(chunks[1][0], chunks[0][1])

    def test_split_text_rejects_invalid_overlap(self) -> None:
        with self.assertRaises(ValueError):
            split_text("sample text", chunk_size=100, chunk_overlap=100)

    def test_chunk_documents_preserves_metadata(self) -> None:
        documents = extract_all_documents(Path("documents"))

        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)

        self.assertGreater(len(chunks), len(documents))
        self.assertTrue(all(chunk.document_name.endswith(".pdf") for chunk in chunks))
        self.assertTrue(all(chunk.page_number >= 1 for chunk in chunks))
        self.assertTrue(all(chunk.text for chunk in chunks))

    def test_write_chunk_output_serializes_chunks(self) -> None:
        documents = extract_all_documents(Path("documents"))
        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "chunks.json"
            write_chunk_output(chunks, output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["chunk_count"], len(chunks))
        self.assertIn("document_name", payload["chunks"][0])
        self.assertIn("page_number", payload["chunks"][0])
        self.assertIn("chunk_index", payload["chunks"][0])
