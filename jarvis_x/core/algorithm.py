import math
import random
import re
from collections import Counter, defaultdict

from jarvis_x.core.config import Config
from jarvis_x.core.semantic_matcher import SemanticMatcher


class LocalAIEngine:
    def __init__(self, kb, semantic_matcher=None, memory_manager=None):
        self.kb = kb
        self.semantic_matcher = semantic_matcher or SemanticMatcher()
        self.memory_manager = memory_manager
        self.documents = []
        self.vocab = set()
        self.idf = {}
        self.doc_vectors = []
        self.markov_model = defaultdict(list)
        self.similarity_threshold = getattr(Config, "SIMILARITY_THRESHOLD", 0.35)

    def rebuild_index(self):
        """Load KB entries and build the TF-IDF and Markov models."""
        self.documents = []
        try:
            cur = self.kb.conn.execute("SELECT pattern, response, confidence, weight FROM knowledge")
            for pattern, response, confidence, weight in cur.fetchall():
                self.documents.append({
                    "text": f"{pattern} {response}",
                    "response": response,
                    "weight": (weight or 1.0) * confidence,
                })
        except Exception:
            pass

        if not self.documents:
            self.documents.append({
                "text": "what is jarvis-x jarvis-x is a local self-learning AI assistant",
                "response": "JARVIS-X is a fully local, self-learning AI assistant running offline.",
                "weight": 1.0,
            })

        all_tokenized = []
        self.vocab = set()
        for doc in self.documents:
            tokens = self._tokenize(doc["text"])
            all_tokenized.append(tokens)
            self.vocab.update(tokens)

        num_docs = len(self.documents)
        self.idf = {}
        for term in self.vocab:
            containing_docs = sum(1 for tokens in all_tokenized if term in tokens)
            self.idf[term] = math.log((1 + num_docs) / (1 + containing_docs)) + 1.0

        self.doc_vectors = []
        for tokens in all_tokenized:
            tf = Counter(tokens)
            vector = {}
            length = 0.0
            for term, count in tf.items():
                tfidf_val = count * self.idf.get(term, 0.0)
                vector[term] = tfidf_val
                length += tfidf_val ** 2

            length = math.sqrt(length)
            if length > 0:
                for term in vector:
                    vector[term] /= length
            self.doc_vectors.append(vector)

        self.markov_model.clear()
        for doc in self.documents:
            words = self._tokenize_raw_case(doc["text"])
            for i in range(len(words) - 1):
                self.markov_model[words[i].lower()].append(words[i + 1])

    def _tokenize(self, text):
        return [w.lower() for w in re.findall(r"\b\w{3,}\b", text)]

    def _tokenize_raw_case(self, text):
        return re.findall(r"\b\w+\b", text)

    def query(self, user_query: str) -> dict:
        """Find the best semantic match and fall back to synthesis when needed."""
        if not self.documents:
            self.rebuild_index()

        normalized_query = (user_query or "").strip()
        query_tokens = self._tokenize(normalized_query)
        expanded_terms = self.semantic_matcher.expand_query(normalized_query)
        if not query_tokens:
            return {"result": "I am listening.", "thoughts": ["Empty query received."]}

        query_tf = Counter(query_tokens)
        query_vector = {}
        query_len = 0.0
        for term, count in query_tf.items():
            tfidf_val = count * self.idf.get(term, 0.0)
            query_vector[term] = tfidf_val
            query_len += tfidf_val ** 2

        query_len = math.sqrt(query_len)
        if query_len > 0:
            for term in query_vector:
                query_vector[term] /= query_len

        best_idx = -1
        best_score = -1.0
        semantic_score = 0.0
        for idx, doc_vector in enumerate(self.doc_vectors):
            score = 0.0
            for term, val in query_vector.items():
                if term in doc_vector:
                    score += val * doc_vector[term]

            score *= self.documents[idx].get("weight", 1.0)
            semantic_bonus = self.semantic_matcher.match_score(normalized_query, self.documents[idx].get("text", "")) * 0.15
            score += semantic_bonus
            if score > best_score:
                best_score = score
                best_idx = idx
                semantic_score = semantic_bonus

        thoughts = [
            "Calculated TF-IDF features over the local knowledge base.",
            f"Top match similarity score: {round(best_score, 4)}",
        ]

        if best_idx != -1 and best_score >= self.similarity_threshold:
            thoughts.append("High similarity confidence. Returning the best indexed response.")
            response = self.documents[best_idx]["response"]
            if self.memory_manager:
                self.memory_manager.store_response(normalized_query, response, best_score)
            return {"result": response, "thoughts": thoughts}

        thoughts.append("Low confidence direct match. Synthesizing a response with the local Markov model.")
        synth_response = self._synthesize(query_tokens or list(expanded_terms))
        if not synth_response and best_idx != -1:
            thoughts.append("Markov chain synthesis failed. Falling back to the strongest partial match.")
            response = self.documents[best_idx]["response"]
            if self.memory_manager:
                self.memory_manager.store_response(normalized_query, response, best_score)
            return {"result": response, "thoughts": thoughts}

        response = synth_response or "I am still learning about that topic. Please teach me by typing: 'remember [fact]'."
        if self.memory_manager:
            self.memory_manager.store_response(normalized_query, response, max(best_score, 0.1))
        return {"result": response, "thoughts": thoughts}

    def _synthesize(self, seeds: list) -> str:
        valid_seeds = [w for w in seeds if w in self.markov_model]
        if not valid_seeds:
            valid_seeds = list(self.markov_model.keys())
            if not valid_seeds:
                return ""

        current_word = random.choice(valid_seeds)
        sentence = [current_word.capitalize()]
        for _ in range(20):
            next_options = self.markov_model.get(current_word.lower())
            if not next_options:
                break
            next_word = random.choice(next_options)
            sentence.append(next_word)
            current_word = next_word
            if next_word.endswith((".", "!", "?")):
                break

        res = " ".join(sentence)
        if not res.endswith((".", "!", "?")):
            res += "."
        return res

    def get_stats(self) -> dict:
        return {"documents": len(self.documents), "vocabulary": len(self.vocab)}
