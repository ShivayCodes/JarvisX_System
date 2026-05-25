import json
import re
from pathlib import Path


LEXICON_DATA = {
    "joy": ["happy", "glad", "great", "awesome", "love", "wonderful", "amazing", "fantastic",
            "excellent", "perfect", "beautiful", "delighted", "thrilled", "excited", "cheerful",
            "thanks", "thank", "perfect", "brilliant", "superb", "pleased", "proud", "fun",
            "welcome", "congrats", "congratulations", "celebrate", "enjoy", "win", "success"],
    "sadness": ["sad", "unhappy", "depressed", "lonely", "hurt", "disappointed", "tired",
                "sorry", "miss", "cry", "tears", "heartbroken", "gloomy", "miserable",
                "regret", "alone", "painful", "sorrow", "grief", "down"],
    "anger": ["angry", "frustrated", "annoyed", "hate", "mad", "furious", "irritated",
              "outraged", "rage", "hostile", "upset", "fuming", "livid", "frustrating",
              "stupid", "terrible", "horrible", "awful", "wrong", "bad"],
    "fear": ["scared", "worried", "anxious", "nervous", "afraid", "stressed", "panicked",
             "terrified", "frightened", "uneasy", "concerned", "doubt", "uncertain",
             "helpless", "panic", "alarmed", "threatened"],
    "surprise": ["wow", "amazing", "unexpected", "shocked", "incredible", "whoa",
                 "surprising", "astonished", "stunned", "speechless", "remarkable",
                 "unbelievable", "sudden", "dramatic", "startled"],
    "trust": ["trust", "believe", "confident", "sure", "certain", "honest", "reliable",
              "faith", "loyal", "dependable", "safe", "secure", "sincere"],
    "neutral": ["ok", "okay", "fine", "alright", "maybe", "continue", "understood",
                "noted", "alright", "right", "correct", "sure"]
}


class EmotionDetector:
    def __init__(self):
        self.lexicon = LEXICON_DATA

    def detect(self, text: str) -> dict:
        if not text:
            return {"neutral": 1.0}
        text_lower = text.lower()
        words = set(re.findall(r'\b[a-z]+\b', text_lower))
        scores = {}
        for emotion, keywords in self.lexicon.items():
            count = sum(1 for kw in keywords if kw in words)
            if count > 0:
                scores[emotion] = count / max(len(words), 1) * 10

        features = {}
        features["caps_ratio"] = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        features["exclamation"] = text.count("!")
        features["question"] = text.count("?")
        features["has_question"] = features["question"] > 0
        features["has_exclamation"] = features["exclamation"] > 0

        if features["has_exclamation"]:
            scores["joy"] = scores.get("joy", 0) + 0.5
            scores["anger"] = scores.get("anger", 0) + 0.3
        if features["has_question"]:
            scores["fear"] = scores.get("fear", 0) + 0.3
            scores["surprise"] = scores.get("surprise", 0) + 0.2
        if features["caps_ratio"] > 0.4 and len(text) > 5:
            scores["anger"] = scores.get("anger", 0) + 1.0

        if not scores:
            return {"neutral": 1.0}

        total = sum(scores.values())
        return {k: round(v / total, 3) for k, v in scores.items()}

    def dominant(self, text: str) -> tuple:
        scores = self.detect(text)
        emotion = max(scores, key=scores.get)
        return emotion, scores[emotion]
