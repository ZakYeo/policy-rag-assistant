import tempfile
import unittest
from pathlib import Path

import chromadb

from app.ingest.chunker import Chunk, chunk_documents
from app.ingest.extractor import extract_all_documents
from app.ingest.indexer import ChunkIndexer, LocalHashEmbedder


class FakeEmbedder:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0, 0.0] for text in texts]


class IndexerTests(unittest.TestCase):
    def test_local_hash_embedder_is_deterministic(self) -> None:
        embedder = LocalHashEmbedder(dimensions=32)

        first = embedder.embed_texts(["same text"])[0]
        second = embedder.embed_texts(["same text"])[0]
        different = embedder.embed_texts(["different text"])[0]

        self.assertEqual(len(first), 32)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)

    def test_upsert_chunks_persists_records(self) -> None:
        documents = extract_all_documents(Path("documents"))
        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name="test_chunks")
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks",
            embedder=FakeEmbedder(),
            collection=collection,
        )

        indexed_count = indexer.upsert_chunks(chunks)

        self.assertEqual(indexed_count, len(chunks))
        self.assertEqual(indexer.count(), len(chunks))

    def test_upsert_chunks_is_idempotent_for_same_ids(self) -> None:
        documents = extract_all_documents(Path("documents"))
        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name="test_chunks")
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks",
            embedder=FakeEmbedder(),
            collection=collection,
        )

        indexer.upsert_chunks(chunks)
        indexer.upsert_chunks(chunks)

        self.assertEqual(indexer.count(), len(chunks))

    def test_upsert_chunks_handles_empty_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            indexer = ChunkIndexer(
                persist_dir=Path(tmpdir),
                collection_name="test_chunks",
                embedder=FakeEmbedder(),
            )

            indexed_count = indexer.upsert_chunks([])

        self.assertEqual(indexed_count, 0)
        self.assertEqual(indexer.count(), 0)

    def test_upsert_chunks_stores_expected_metadata(self) -> None:
        chunk = Chunk(
            chunk_id="doc-1-p1-c0",
            document_id="doc-1",
            document_name="doc-1.pdf",
            source_path="documents/doc-1.pdf",
            page_number=1,
            chunk_index=0,
            char_start=0,
            char_end=12,
            text="sample chunk",
        )
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name="test_chunks")
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks",
            embedder=FakeEmbedder(),
            collection=collection,
        )

        indexer.upsert_chunks([chunk])
        result = collection.get(ids=[chunk.chunk_id], include=["metadatas", "documents"])

        self.assertEqual(result["documents"][0], "sample chunk")
        self.assertEqual(result["metadatas"][0]["document_name"], "doc-1.pdf")
        self.assertEqual(result["metadatas"][0]["page_number"], 1)

    def test_reset_clears_indexed_records(self) -> None:
        documents = extract_all_documents(Path("documents"))
        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(name="test_chunks")
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks",
            embedder=FakeEmbedder(),
            collection=collection,
        )

        indexer.upsert_chunks(chunks)
        indexer.reset()

        self.assertEqual(indexer.count(), 0)
