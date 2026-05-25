import time
from collections import deque
from typing import Optional


class ReflectionEngine:
    def __init__(self, max_log: int = 50):
        self.failure_log = deque(maxlen=max_log)
        self.success_log = deque(maxlen=max_log)

    def record_outcome(self, action: str, success: bool, duration_ms: float = 0, error: str = ""):
        entry = {
            "action": action,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": time.time()
        }
        if success:
            self.success_log.append(entry)
        else:
            self.failure_log.append(entry)

    def evaluate(self, action: str, response: str) -> Optional[str]:
        if "error" in response.lower() or "failed" in response.lower() or "not implemented" in response.lower():
            suggestion = self._suggest_alternative(action)
            self.record_outcome(action, False, error=response)
            return suggestion
        self.record_outcome(action, True)
        return None

    def _suggest_alternative(self, action: str) -> str:
        suggestions = {
            "web_scrape": "Try 'open site [url]' to open it in your browser instead.",
            "find_files": "Try 'system info' to see system status first.",
            "unknown": "Try 'help' to see available commands.",
        }
        return suggestions.get(action, "")

    def get_failure_rate(self, action: str = "") -> float:
        source = [e for e in self.failure_log if not action or e["action"] == action]
        successes = [e for e in self.success_log if not action or e["action"] == action]
        total = len(source) + len(successes)
        if total == 0:
            return 0.0
        return len(source) / total

    def summary(self) -> dict:
        return {
            "total_failures": len(self.failure_log),
            "total_successes": len(self.success_log),
            "failure_rate": round(self.get_failure_rate(), 3),
            "recent_failures": list(self.failure_log)[-5:]
        }
