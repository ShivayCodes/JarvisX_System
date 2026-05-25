from collections import deque
from typing import List, Dict, Optional


class ConversationContext:
    def __init__(self, max_size: int = 50):
        self.history = deque(maxlen=max_size)
        self.current_topic = None
        self.last_intent = None

    def record(self, text: str, response: str, intent: str = "", emotion: str = ""):
        entry = {
            "text": text,
            "response": response,
            "intent": intent,
            "emotion": emotion
        }
        self.history.append(entry)
        self.last_intent = intent or self.last_intent

        if len(text) > 3:
            words = text.lower().split()
            if intent in ("unknown", "greet", "help"):
                return
            topic_words = [w for w in words if len(w) > 4]
            if topic_words:
                self.current_topic = topic_words[-1]

    def recent(self, limit: int = 5) -> List[Dict]:
        return list(self.history)[-limit:]

    def get_context_summary(self) -> str:
        if not self.history:
            return ""
        last = self.history[-1]
        parts = []
        if self.current_topic:
            parts.append(f"topic: {self.current_topic}")
        if last.get("emotion"):
            parts.append(f"mood: {last['emotion']}")
        if self.last_intent:
            parts.append(f"last_action: {self.last_intent}")
        return " | ".join(parts) if parts else ""

    def clear(self):
        self.history.clear()
        self.current_topic = None
        self.last_intent = None
