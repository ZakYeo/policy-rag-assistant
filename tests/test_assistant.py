import unittest

from app.assistant import AssistantService


class FakeRetriever:
    def retrieve(self, query: str, top_k: int):
        self.last_query = query
        self.last_top_k = top_k
        return [
            type(
                "Chunk",
                (),
                {
                    "chunk_id": "chunk-1",
                    "document_name": "policy.pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "distance": 0.1,
                    "text": "policy text",
                },
            )()
        ]


class FakeAnswerer:
    def answer(self, question: str, chunks):
        self.last_question = question
        self.last_chunks = chunks
        return type(
            "AnswerResult",
            (),
            {
                "answer": "Test answer",
                "provider": "extractive",
                "sources": [
                    type(
                        "Source",
                        (),
                        {
                            "document_name": "policy.pdf",
                            "page_number": 1,
                            "chunk_id": "chunk-1",
                        },
                    )()
                ],
            },
        )()


class AssistantServiceTests(unittest.TestCase):
    def test_answer_question_returns_serialized_response(self) -> None:
        retriever = FakeRetriever()
        answerer = FakeAnswerer()
        service = AssistantService(retriever=retriever, answerer=answerer)

        response = service.answer_question("What is the rule?", top_k=2)

        self.assertEqual(response.answer, "Test answer")
        self.assertEqual(response.answer_provider, "extractive")
        self.assertEqual(response.sources[0]["document_name"], "policy.pdf")
        self.assertEqual(response.retrieved_chunks[0]["chunk_id"], "chunk-1")
        self.assertEqual(retriever.last_top_k, 2)

    def test_answer_question_rejects_blank_input(self) -> None:
        service = AssistantService(retriever=FakeRetriever(), answerer=FakeAnswerer())

        with self.assertRaises(ValueError):
            service.answer_question("   ")
