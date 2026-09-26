"""Greeting skill for JARVIS-X."""
import random


greetings_db = [
    "Hello! I'm JARVIS-X, your local AI assistant. How can I help?",
    "Hi there! Ready to assist with whatever you need.",
    "Greetings! What can I do for you today?",
    "Hey! Nice to meet you. What's on your mind?"
]


def process(query: str, context: list, memory) -> str:
    """
    Process a greeting.
    
    Args:
        query: User query.
        context: Retrieved context.
        memory: Memory store.
        
    Returns:
        str: Greeting response.
    """
    return random.choice(greetings_db)


def register(engine):
    """Register the greeting skill."""
    engine.skills.register("greeting", process)
