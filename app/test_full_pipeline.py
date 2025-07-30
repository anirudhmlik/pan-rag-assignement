import unittest
import asyncio
from pathlib import Path

from app.services.ingest import process_document
from app.services.retriever import retrieve_chunks
from app.services.llm import generate_response

TEST_PDF_PATH = "test_document.pdf"

class TestFullDocumentPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not Path(TEST_PDF_PATH).exists():
            raise FileNotFoundError(f"Missing test file: {TEST_PDF_PATH}")

        with open(TEST_PDF_PATH, "rb") as f:
            cls.test_bytes = f.read()

    def test_01_ingest_document(self):
        async def run():
            result = await process_document(self.test_bytes, "test_document.pdf")
            self.assertEqual(result["status"], "completed")
            self.assertGreater(result["num_chunks"], 0)

        asyncio.run(run())

    def test_02_retrieve_and_respond(self):
        async def run():
            query = "What is this document about?"
            chunks = await retrieve_chunks(query)
            self.assertGreater(len(chunks), 0)

            response = await generate_response(query, chunks)
            print("\n[LLM RESPONSE]:", response)
            self.assertIsInstance(response, str)
            self.assertGreater(len(response.strip()), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()