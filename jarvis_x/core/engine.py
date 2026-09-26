"""Core JARVIS-X engine."""
import json
from datetime import datetime
from jarvis_x.core.config import Config
from jarvis_x.nlp.intent_parser import IntentParser
from jarvis_x.memory.store import MemoryStore
from jarvis_x.skills.registry import SkillRegistry


class JarvisEngine:
    """Main JARVIS-X processing engine."""

    def __init__(self):
        """Initialize the JARVIS-X engine."""
        Config.ensure_directories()
        self.intent_parser = IntentParser()
        self.memory = MemoryStore()
        self.skills = SkillRegistry()
        self.conversation_history = []
        self.kb = self  # For backward compatibility
        self.local_ai = self  # For backward compatibility

    def process(self, query: str) -> str:
        """
        Process a user query and generate a response.
        
        Args:
            query: User input query.
            
        Returns:
            str: Assistant response.
        """
        # Store in history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "content": query
        })

        # Parse intent
        intent = self.intent_parser.parse(query)
        
        # Check memory for context
        context = self.memory.search(query, limit=3)
        
        # Execute skill if matched
        if intent.get("skill"):
            skill_name = intent["skill"]
            skill = self.skills.get(skill_name)
            if skill:
                response = skill(query, context, self.memory)
            else:
                response = f"Skill '{skill_name}' not found."
        else:
            # Default response
            response = self._generate_response(query, intent, context)

        # Store response
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": response
        })

        # Save to memory
        self.memory.store({
            "query": query,
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })

        return response

    def _generate_response(self, query: str, intent: dict, context: list) -> str:
        """
        Generate a response based on intent and context.
        
        Args:
            query: Original query.
            intent: Parsed intent.
            context: Retrieved context items.
            
        Returns:
            str: Generated response.
        """
        if intent.get("type") == "greeting":
            return "Hello! I'm JARVIS-X. How can I help you today?"
        elif intent.get("type") == "question":
            if context:
                return f"Based on my knowledge: {context[0].get('content', 'I found some information but cannot retrieve it right now.')}"
            return "I'm not sure about that. Could you provide more details?"
        elif intent.get("type") == "command":
            return f"Executing command: {intent.get('target', 'unknown')}"
        else:
            return "I understand. Can you tell me more?"

    def get_stats(self) -> str:
        """Get engine statistics."""
        stats = {
            "conversation_turns": len(self.conversation_history),
            "memory_items": self.memory.count(),
            "skills_registered": len(self.skills.registry),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(stats, indent=2)
