"""Intent parsing for user queries."""
import re


class IntentParser:
    """Parses user intent from queries."""

    def __init__(self):
        """Initialize the intent parser."""
        self.greetings = ["hello", "hi", "hey", "greetings", "good morning"]
        self.questions = ["what", "how", "why", "where", "when", "who", "?"]
        self.commands = ["do", "execute", "run", "start", "stop", "remember"]

    def parse(self, query: str) -> dict:
        """
        Parse intent from a query.
        
        Args:
            query: User query string.
            
        Returns:
            dict: Intent data with type, confidence, and optional skill.
        """
        query_lower = query.lower().strip()
        
        intent = {
            "type": "unknown",
            "confidence": 0.0,
            "skill": None,
            "raw_query": query
        }
        
        # Check for greetings
        for greeting in self.greetings:
            if query_lower.startswith(greeting):
                intent["type"] = "greeting"
                intent["confidence"] = 0.95
                return intent
        
        # Check for questions
        if any(q in query_lower for q in self.questions):
            intent["type"] = "question"
            intent["confidence"] = 0.85
            return intent
        
        # Check for commands
        for cmd in self.commands:
            if query_lower.startswith(cmd):
                intent["type"] = "command"
                intent["confidence"] = 0.8
                intent["target"] = query_lower[len(cmd):].strip()
                return intent
        
        # Default to statement
        intent["type"] = "statement"
        intent["confidence"] = 0.5
        return intent
