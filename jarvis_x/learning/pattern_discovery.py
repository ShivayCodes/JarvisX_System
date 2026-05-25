import re
from collections import Counter
from typing import List, Dict, Optional

from jarvis_x.memory.store import KnowledgeBase


class PatternDiscovery:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def find_repeated_queries(self, min_count: int = 3) -> List[Dict]:
        cur = self.kb.conn.execute(
            "SELECT user_input, COUNT(*) as cnt FROM interactions "
            "GROUP BY user_input HAVING cnt >= ? ORDER BY cnt DESC LIMIT 20",
            (min_count,)
        )
        return [{"query": r["user_input"], "count": r["cnt"]} for r in cur.fetchall()]

    def suggest_shortcuts(self, min_count: int = 3) -> List[Dict]:
        patterns = self.find_repeated_queries(min_count)
        suggestions = []
        for p in patterns:
            intent = self.kb.recall(p["query"])
            if not intent:
                suggestions.append({
                    "pattern": p["query"],
                    "count": p["count"],
                    "suggestion": f"Consider: 'remember {p['query']}' to auto-answer this"
                })
        return suggestions

    def auto_learn_patterns(self, dry_run: bool = True) -> int:
        suggestions = self.suggest_shortcuts()
        learned = 0
        for s in suggestions:
            if not dry_run:
                self.kb.learn(s["pattern"], f"Auto: {s['pattern']}", confidence=0.4)
                self.kb.log_learning("auto_pattern", s["pattern"])
            learned += 1
        return learned
