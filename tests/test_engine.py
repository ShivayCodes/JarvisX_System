"""Tests for the JARVIS-X engine."""
import unittest
from jarvis_x.core.engine import JarvisEngine
from jarvis_x.nlp.intent_parser import IntentParser


class TestJarvisEngine(unittest.TestCase):
    """Test suite for JarvisEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = JarvisEngine()
        self.parser = IntentParser()

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertIsNotNone(self.engine.memory)
        self.assertIsNotNone(self.engine.skills)
        self.assertEqual(len(self.engine.conversation_history), 0)

    def test_intent_parsing_greeting(self):
        """Test greeting intent detection."""
        intent = self.parser.parse("hello")
        self.assertEqual(intent["type"], "greeting")
        self.assertGreater(intent["confidence"], 0.8)

    def test_intent_parsing_question(self):
        """Test question intent detection."""
        intent = self.parser.parse("What is AI?")
        self.assertEqual(intent["type"], "question")

    def test_query_processing(self):
        """Test basic query processing."""
        response = self.engine.process("hello")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)
        self.assertEqual(len(self.engine.conversation_history), 2)  # User + Assistant


if __name__ == "__main__":
    unittest.main()
