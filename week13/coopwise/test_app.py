from __future__ import annotations

import unittest

import app
from build_index import chunk_text, load_sources


class CoopWiseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_sources()

    def test_corpus_size(self):
        self.assertGreaterEqual(len(self.sources), 20)
        self.assertLessEqual(len(self.sources), 30)

    def test_required_metadata(self):
        for source in self.sources:
            for field in ("title", "organization", "topic", "url", "text"):
                self.assertTrue(source[field].strip())

    def test_empty_query_is_handled(self):
        output = app.search("   ", "All topics")
        self.assertIn("Enter a question", output)

    def test_search_returns_top_five_or_available_count(self):
        if app.COLLECTION is None:
            self.skipTest("Saved database is not present")
        output = app.search("How do I keep the coop dry in winter?", "All topics")
        self.assertNotIn("Enter a question", output)
        self.assertNotIn("Search index unavailable", output)


if __name__ == "__main__":
    unittest.main()
