import re
import time
from collections import Counter
from typing import Optional, List, Dict, Tuple

from .pattern_discovery import PatternDiscovery
from .feedback import FeedbackHandler
from .dataset_learner import DatasetLearner
from jarvis_x.memory.store import KnowledgeBase


EXTRACTION_PATTERNS = [
    (r'(?:my|the)\s+(\w+(?:\s+\w+){0,3})\s+is\s+(\w+(?:\s+\w+){0,5})', 'my_{0}={1}'),
    (r'i\s+(?:have|got)\s+(\w+(?:\s+\w+){0,3})\s+(?:at|on|in|for)\s+(.+)', 'schedule_{0}={1}'),
    (r'\b(\w+)\s+is\s+my\s+favou?rite\s+(\w+)', 'favorite_{0}={1}'),
    (r'i\s+(?:like|love|enjoy)\s+(.+)', 'user_likes={0}'),
    (r'i\s+am\s+feeling\s+(\w+)', 'user_mood={0}'),
    (r'i\s+feel\s+(\w+)', 'user_mood={0}'),
    (r'i\s+am\s+(\w+)', 'user_mood={0}'),
    (r'my\s+name\s+is\s+(.+)', 'user_name={0}'),
    (r'i\s+am\s+(\d+)\s+years?\s+old', 'user_age={0}'),
    (r'i\s+(?:work|job|role)\s+(?:as|at|in)\s+(.+)', 'user_work={0}'),
    (r'(?:call|name)\s+me\s+(\w+)', 'user_nickname={0}'),
    (r'(\w+(?:\s+\w+)?)\s+is\s+(?:my|the)\s+best\s+(\w+)', 'best_{0}={1}'),
]


CORRECTION_PATTERNS = [
    r'(?:no|wrong|incorrect|not\s+that|that\'?s?\s+not\s+right|actually|rather)',
    r'(?:i\s+meant|i\s+said|let\s+me\s+clarify|instead\s+of|not)',
]


class SelfLearning:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.pattern_discovery = PatternDiscovery(kb)
        self.feedback = FeedbackHandler(kb)
        self.dataset_learner = DatasetLearner(kb)
        self._cycle_counter = 0
        self._learned_phrasings = {}
        self._last_neg_feedback = False
        self._last_query = ""
        self._last_response = ""

    def extract_facts(self, text: str) -> List[str]:
        extracted = []
        text_lower = text.lower()
        seen_keys = set()
        for pattern, template in EXTRACTION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                fact_key = template.format(*[g.strip() for g in groups])
                if fact_key in seen_keys:
                    continue
                seen_keys.add(fact_key)
                fact_value = groups[-1].strip()
                self.kb.learn(fact_key.replace("_", " "), fact_value, confidence=0.6)
                self.kb.log_learning("passive_extract", f"{fact_key} -> {fact_value}")
                extracted.append(f"{fact_key}: {fact_value}")
        return extracted

    def is_correction(self, text: str) -> bool:
        text_lower = text.lower()
        for pattern in CORRECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def handle_correction(self, text: str) -> Optional[str]:
        if not self._last_query or not self._last_response:
            return None
        if not self._last_neg_feedback:
            return None

        if self.is_correction(text):
            correction = re.sub(
                r'(?:no|wrong|incorrect|not\s+that|actually|rather|i\s+meant|i\s+said|let\s+me\s+clarify)[\s,.;!?]*',
                '', text, flags=re.IGNORECASE
            ).strip(', .;!? \t')
            if correction:
                self.kb.learn(self._last_query, f"Corrected: {correction}", confidence=0.8)
                self.kb.log_learning("correction", f"'{self._last_query}' -> '{correction}'")
                self._last_neg_feedback = False
                return correction
        return None

    def learn_phrasing(self, text: str, intent_action: str, confidence: float):
        words = text.lower().split()
        key_words = [w for w in words if len(w) > 3 and w not in
                     ("what", "where", "when", "why", "how", "the", "this", "that",
                      "with", "from", "have", "been", "were", "could", "would", "should",
                      "tell", "show", "give", "make", "find", "search", "open", "type",
                      "click", "remember", "recall", "learn", "help", "hello", "quit",
                      "exit", "shutdown", "goodbye", "please", "thanks")]
        if len(key_words) < 2 or len(key_words) > 6:
            return

        phrasing_key = " ".join(key_words)
        if phrasing_key not in self._learned_phrasings:
            self._learned_phrasings[phrasing_key] = {
                "action": intent_action,
                "count": 0,
                "confidence": confidence,
            }
            if intent_action not in ("unknown", "greet", "shutdown", "feedback_positive", "feedback_negative"):
                self.kb.learn(phrasing_key, intent_action, confidence=max(0.3, confidence * 0.6))
                self.kb.log_learning("new_phrasing", f"'{phrasing_key}' -> {intent_action}")

    def reinforce(self, user_input: str, response: str, positive: bool):
        if not user_input or not response:
            return

        self.feedback.record(user_input, positive)
        delta = 0.1 if positive else -0.1
        self.kb.adjust_confidence(user_input, delta)

        if positive:
            current = self.kb.get_confidence(user_input)
            self.kb.learn(user_input, response, confidence=current)
            self.kb.log_learning("reinforce_positive", user_input)
        else:
            self.kb.log_learning("reinforce_negative", user_input)
            self._last_neg_feedback = True

    def auto_improve(self, dry_run: bool = False) -> int:
        self._cycle_counter += 1
        if self._cycle_counter % 3 != 0:
            return 0

        total = 0
        learned = self.pattern_discovery.auto_learn_patterns(dry_run=dry_run)
        total += learned

        if learned and not dry_run:
            self.kb.log_learning("self_improve", f"pattern_discovery: {learned}")

        if self._cycle_counter % 10 == 0 and not dry_run:
            self._prune_low_confidence()

        return total

    def _prune_low_confidence(self):
        cur = self.kb.conn.execute(
            "SELECT id, pattern, confidence FROM knowledge WHERE confidence < 0.1"
        )
        count = 0
        for row in cur.fetchall():
            with self.kb.conn:
                self.kb.conn.execute("DELETE FROM knowledge WHERE id = ?", (row["id"],))
            count += 1
        if count:
            self.kb.log_learning("prune", f"removed {count} low-confidence patterns")

    def extract_and_learn(self, text: str, intent_action: str, confidence: float) -> List[str]:
        facts = self.extract_facts(text)
        self.learn_phrasing(text, intent_action, confidence)
        return facts

    def summarize(self) -> str:
        repeated = self.pattern_discovery.find_repeated_queries(min_count=2)
        stats = self.kb.get_stats()
        lines = [
            f"Interactions stored: {stats.get('interactions', 0)}",
            f"Facts learned: {stats.get('facts', 0)}",
            f"Learned phrasings: {len(self._learned_phrasings)}",
        ]
        if repeated:
            lines.append("\nRepeated queries I can learn from:")
            for item in repeated[:5]:
                lines.append(f"  '{item['query']}' ({item['count']}x)")
        else:
            lines.append("\nKeep talking to me so I can learn patterns.")
        return "\n".join(lines)

    def learn_from_dataset(self, path: str) -> str:
        try:
            count = self.dataset_learner.learn_from_path(path)
            if count:
                return f"Learned {count} entries from dataset: {path}"
            return f"No supported XML/HTML entries found at: {path}"
        except Exception as exc:
            return f"Dataset learning failed: {exc}"

    def set_context(self, last_query: str, last_response: str):
        self._last_query = last_query
        self._last_response = last_response
