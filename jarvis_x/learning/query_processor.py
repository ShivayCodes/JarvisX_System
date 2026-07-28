import re


class QueryProcessor:
    """Simple local intent classification and normalization."""

    def normalize(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text.strip())
        cleaned = cleaned.replace("can't", "cannot")
        return cleaned

    def classify_intent(self, text: str) -> str:
        lowered = self.normalize(text).lower()
        if re.search(r"\b(hello|hi|hey)\b", lowered):
            return "greeting"
        if re.search(r"\b(help|assist|support)\b", lowered):
            return "help"
        if re.search(r"\b(remember|learn)\b", lowered):
            return "learn"
        if re.search(r"\b(recall|know about)\b", lowered):
            return "recall"
        if re.search(r"\b(open|launch|start)\b", lowered):
            return "command"
        return "unknown"
