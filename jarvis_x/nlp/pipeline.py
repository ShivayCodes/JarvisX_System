from jarvis_x.nlp.intent import IntentParser
from jarvis_x.nlp.sentiment import SentimentAnalyzer


class NLPPipeline:
    def __init__(self):
        self.sentiment = SentimentAnalyzer()

    def parse(self, text: str) -> object:
        intent = IntentParser.parse(text)
        sentiment = self.sentiment.analyze(text)
        intent.emotion = sentiment.get("emotion", "neutral")
        intent.sentiment = sentiment.get("compound", 0.0)
        return intent
