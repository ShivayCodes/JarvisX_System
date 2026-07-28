import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis_x.core.algorithm import LocalAIEngine
from jarvis_x.core.semantic_matcher import SemanticMatcher
from jarvis_x.learning.dataset_validator import DatasetValidator
from jarvis_x.core.memory_manager import MemoryManager
from jarvis_x.memory.store import KnowledgeBase


class LocalAIGTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = os.path.join(self.temp_dir.name, "memory.db")
        self.kb = KnowledgeBase.__new__(KnowledgeBase)
        self.kb.conn = None
        self.kb.learn = lambda *args, **kwargs: None
        self.kb.get_stats = lambda: {"interactions": 0, "facts": 0, "emotions": {}}

    def test_semantic_matcher_expands_and_scores(self):
        matcher = SemanticMatcher()
        score = matcher.match_score("what is the weather", "weather report")
        self.assertGreater(score, 0.0)
        expanded = matcher.expand_query("what is the weather")
        self.assertTrue(any(term in expanded for term in ["weather", "forecast"]))

    def test_dataset_validator_handles_json_and_txt(self):
        root = Path(self.temp_dir.name)
        (root / "sample.json").write_text('{"faq": [{"question": "What is AI?", "answer": "Artificial intelligence."}] }', encoding="utf-8")
        (root / "notes.txt").write_text("Local AI runs offline.", encoding="utf-8")
        validator = DatasetValidator(root)
        report = validator.validate_directory(root)
        self.assertGreaterEqual(report["files_scanned"], 2)
        self.assertEqual(report["errors"], [])

    def test_local_ai_synthesizes_and_ranks(self):
        engine = LocalAIEngine(kb=self.kb)
        engine.documents = [
            {"text": "jarvis-x is a local assistant", "response": "Local assistant", "weight": 1.0},
            {"text": "weather forecast is useful", "response": "Weather forecast", "weight": 1.0},
        ]
        engine.vocab = set(["jarvis", "assistant", "weather", "forecast"])
        engine.idf = {"jarvis": 1.0, "assistant": 1.0, "weather": 1.0, "forecast": 1.0}
        engine.doc_vectors = [{"jarvis": 1.0, "assistant": 1.0}, {"weather": 1.0, "forecast": 1.0}]
        engine.markov_model = {"weather": ["forecast"], "forecast": ["is"]}
        result = engine.query("jarvis assistant")
        self.assertIn("result", result)
        self.assertTrue(result["result"])


if __name__ == "__main__":
    unittest.main()
