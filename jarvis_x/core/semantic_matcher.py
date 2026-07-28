import re
from typing import List, Set


class SemanticMatcher:
    """Lightweight offline semantic matching helpers."""

    def __init__(self):
        self.thesaurus = {
            "weather": {"weather", "forecast", "climate"},
            "hello": {"hello", "hi", "greet"},
            "help": {"help", "assist", "support"},
            "remember": {"remember", "store", "learn"},
            "open": {"open", "launch", "start"},
        }

    def _tokens(self, text: str) -> Set[str]:
        return {token for token in re.findall(r"\b\w+\b", text.lower()) if len(token) > 2}

    def expand_query(self, query: str) -> Set[str]:
        tokens = self._tokens(query)
        expanded = set(tokens)
        for token in list(tokens):
            expanded.update(self.thesaurus.get(token, set()))
        return expanded

    def match_score(self, query: str, candidate: str) -> float:
        query_terms = self.expand_query(query)
        candidate_terms = self.expand_query(candidate)
        if not query_terms and not candidate_terms:
            return 0.0
        overlap = len(query_terms & candidate_terms)
        union = len(query_terms | candidate_terms)
        return overlap / union if union else 0.0
