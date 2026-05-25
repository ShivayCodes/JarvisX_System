import re
from typing import Optional


class IntentResult:
    def __init__(self, action: str = "unknown", confidence: float = 0.0, entities: dict = None,
                 raw: str = "", emotion: str = "neutral", sentiment: float = 0.0):
        self.action = action
        self.confidence = confidence
        self.entities = entities or {}
        self.raw = raw
        self.emotion = emotion
        self.sentiment = sentiment


class IntentParser:
    PATTERNS = [
        (r'(open|go to|visit|navigate)\s+(?:site|website|page|url)?\s*(https?://[^\s]+)', 'web_open', {'url': 2}),
        (r'(scrape|extract)\s+from\s+(https?://[^\s]+)\s+using\s+(.+)', 'web_scrape', {'url': 1, 'selector': 2}),
        (r'(system|computer)\s+(info|status|spec)', 'sys_info', {}),
        (r'(find|search)\s+files?\s+for\s+(.+)', 'find_files', {'query': 2}),
        (r'(hello|hi|hey|good morning|good evening)', 'greet', {}),
        (r'(help|what can you do|commands)', 'help', {}),
        (r'(?:load|learn|ingest)\s+(?:dataset|data)\s+(?:from\s+)?(.+)', 'load_dataset', {'path': 1}),
        (r'(self[- ]?learn|auto[- ]?learn|learn from history|train yourself|improve yourself)', 'self_learn', {}),
        (r'(remember|learn)\s+(.+)', 'learn', {'fact': 2}),
        (r'(what do you know about|recall)\s+(.+)', 'recall', {'topic': 2}),
        (r'(\+1|good|thanks|thank you|nice|great|awesome|well done)', 'feedback_positive', {}),
        (r'(-1|bad|wrong|no|incorrect|terrible|hate)', 'feedback_negative', {}),
        (r'(quit|exit|shutdown|goodbye|bye)', 'shutdown', {}),
    ]

    @classmethod
    def parse(cls, text: str) -> IntentResult:
        text_lower = text.lower().strip()
        result = IntentResult(raw=text)

        for pattern, action, entity_map in cls.PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                conf = min(1.0, len(match.groups()) * 0.3 + 0.5)
                if conf > result.confidence:
                    result.action = action
                    result.confidence = conf
                    for ent_name, group_idx in entity_map.items():
                        if group_idx <= len(match.groups()):
                            result.entities[ent_name] = match.group(group_idx)
        return result
