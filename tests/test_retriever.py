import unittest
from pathlib import Path

import chromadb

from app.ingest.chunker import Chunk, chunk_documents
from app.ingest.extractor import extract_all_documents
from app.ingest.indexer import ChunkIndexer
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.retriever import ChunkRetriever


class KeywordEmbedder:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            if "alpha" in lower:
                vectors.append([1.0, 0.0, 0.0])
            elif "beta" in lower:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


class RetrieverTests(unittest.TestCase):
    def test_retrieve_returns_best_matching_chunk(self) -> None:
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(
            name="test_chunks_keyword_match",
            metadata={"hnsw:space": "cosine"},
        )
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks_keyword_match",
            embedder=KeywordEmbedder(),
            collection=collection,
        )
        retriever = ChunkRetriever(
            persist_dir=Path("."),
            collection_name="test_chunks_keyword_match",
            embedder=KeywordEmbedder(),
            collection=collection,
        )
        indexer.upsert_chunks(
            [
                Chunk(
                    chunk_id="alpha-1",
                    document_id="alpha",
                    document_name="alpha.pdf",
                    source_path="documents/alpha.pdf",
                    page_number=1,
                    chunk_index=0,
                    char_start=0,
                    char_end=12,
                    text="alpha policy guidance",
                ),
                Chunk(
                    chunk_id="beta-1",
                    document_id="beta",
                    document_name="beta.pdf",
                    source_path="documents/beta.pdf",
                    page_number=1,
                    chunk_index=0,
                    char_start=0,
                    char_end=12,
                    text="beta policy guidance",
                ),
            ]
        )

        results = retriever.retrieve("alpha question", top_k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "alpha-1")
        self.assertEqual(results[0].document_name, "alpha.pdf")

    def test_retrieve_returns_empty_for_blank_query(self) -> None:
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(
            name="test_chunks_blank_query",
            metadata={"hnsw:space": "cosine"},
        )
        retriever = ChunkRetriever(
            persist_dir=Path("."),
            collection_name="test_chunks_blank_query",
            embedder=KeywordEmbedder(),
            collection=collection,
        )

        results = retriever.retrieve("   ", top_k=3)

        self.assertEqual(results, [])

    def test_retrieve_returns_metadata_for_real_chunks(self) -> None:
        documents = extract_all_documents(Path("documents"))
        chunks = chunk_documents(documents, chunk_size=500, chunk_overlap=50)
        client = chromadb.EphemeralClient()
        collection = client.get_or_create_collection(
            name="test_chunks_real_docs",
            metadata={"hnsw:space": "cosine"},
        )
        embedder = LocalHashEmbedder(dimensions=64)
        indexer = ChunkIndexer(
            persist_dir=Path("."),
            collection_name="test_chunks_real_docs",
            embedder=embedder,
            collection=collection,
        )
        retriever = ChunkRetriever(
            persist_dir=Path("."),
            collection_name="test_chunks_real_docs",
            embedder=embedder,
            collection=collection,
        )
        indexer.upsert_chunks(chunks)

        results = retriever.retrieve("What does the policy say about confidential information?", top_k=3)

        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(results[0].document_name.endswith(".pdf"))
        self.assertGreaterEqual(results[0].page_number, 1)
        self.assertTrue(results[0].text)
