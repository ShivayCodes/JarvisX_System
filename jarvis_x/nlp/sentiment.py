import re

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _HAS_VADER = True
except ImportError:
    _HAS_VADER = False

from jarvis_x.emotion.detector import EmotionDetector


class SentimentAnalyzer:
    def __init__(self):
        self.emotion = EmotionDetector()
        self._vader = None
        if _HAS_VADER:
            try:
                self._vader = SentimentIntensityAnalyzer()
            except LookupError:
                pass

    def analyze(self, text: str) -> dict:
        if not text:
            return {"compound": 0.0, "emotion": "neutral", "confidence": 0.0}

        result = {"compound": 0.0}

        if self._vader:
            vader_scores = self._vader.polarity_scores(text)
            result["compound"] = vader_scores["compound"]
            result["pos"] = vader_scores["pos"]
            result["neg"] = vader_scores["neg"]
            result["neu"] = vader_scores["neu"]

        emotion, conf = self.emotion.dominant(text)
        result["emotion"] = emotion
        result["confidence"] = conf

        if result.get("compound", 0) > 0.5 and emotion == "neutral":
            result["emotion"] = "joy"
        elif result.get("compound", 0) < -0.5 and emotion == "neutral":
            result["emotion"] = "sadness"

        return result
