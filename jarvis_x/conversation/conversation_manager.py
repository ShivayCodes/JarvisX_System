from collections import deque
from typing import Deque, Dict, List


class ConversationManager:
    """Track simple conversation state for offline multi-turn interactions."""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.turns: Deque[Dict[str, str]] = deque(maxlen=max_turns)

    def add_turn(self, user_msg: str, bot_response: str):
        self.turns.append({"user": user_msg, "bot": bot_response})

    def last_context(self) -> List[Dict[str, str]]:
        return list(self.turns)
