import re
import math
from collections import Counter, defaultdict
import random

class LocalAIEngine:
    def __init__(self, kb):
        self.kb = kb
        self.documents = []  # List of dicts: {"text": str, "source": str, "metadata": dict}
        self.vocab = set()
        self.idf = {}
        self.doc_vectors = []
        self.markov_model = defaultdict(list)
        
    def rebuild_index(self):
        """
        Loads all knowledge entries from KB and files, and trains the TF-IDF and Markov models.
        """
        # Fetch entries from knowledge base sqlite
        self.documents = []
        try:
            cur = self.kb.conn.execute("SELECT pattern, response, confidence, weight FROM knowledge")
            for pattern, response, confidence, weight in cur.fetchall():
                # Add pattern + response as documents
                self.documents.append({
                    "text": f"{pattern} {response}",
                    "response": response,
                    "weight": (weight or 1.0) * confidence
                })
        except Exception:
            pass

        if not self.documents:
            # Add fallback basic information
            self.documents.append({
                "text": "what is jarvis-x jarvis-x is a local self-learning AI assistant",
                "response": "JARVIS-X is a fully local, self-learning AI assistant running offline.",
                "weight": 1.0
            })

        # Tokenize and build vocabulary
        all_tokenized = []
        self.vocab = set()
        for doc in self.documents:
            tokens = self._tokenize(doc["text"])
            all_tokenized.append(tokens)
            self.vocab.update(tokens)

        # Calculate IDF
        num_docs = len(self.documents)
        self.idf = {}
        for term in self.vocab:
            containing_docs = sum(1 for tokens in all_tokenized if term in tokens)
            self.idf[term] = math.log((1 + num_docs) / (1 + containing_docs)) + 1.0

        # Calculate Doc Vectors (normalized TF-IDF)
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

        # Build Markov Chain from all document texts
        self.markov_model.clear()
        for doc in self.documents:
            words = self._tokenize_raw_case(doc["text"])
            for i in range(len(words) - 1):
                self.markov_model[words[i].lower()].append(words[i+1])
                
    def _tokenize(self, text):
        return [w.lower() for w in re.findall(r'\b\w{3,}\b', text)]

    def _tokenize_raw_case(self, text):
        return re.findall(r'\b\w+\b', text)

    def query(self, user_query: str) -> dict:
        """
        Finds the best semantic match. If score is high enough, return it.
        Otherwise, synthesize a response using Markov chains + TF-IDF contexts.
        """
        if not self.documents:
            self.rebuild_index()

        query_tokens = self._tokenize(user_query)
        if not query_tokens:
            return {"result": "I am listening.", "thoughts": ["Empty query received."]}

        # Compute query vector
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

        # Calculate Cosine Similarities
        best_idx = -1
        best_score = -1.0
        
        for idx, doc_vector in enumerate(self.doc_vectors):
            score = 0.0
            for term, val in query_vector.items():
                if term in doc_vector:
                    score += val * doc_vector[term]
            
            # Apply DB learning weights
            score *= self.documents[idx].get("weight", 1.0)
            
            if score > best_score:
                best_score = score
                best_idx = idx

        thoughts = [
            f"Calculated TF-IDF features over database.",
            f"Top match similarity score: {round(best_score, 4)}"
        ]

        # Threshold for direct match response
        if best_score > 0.35 and best_idx != -1:
            thoughts.append("High similarity confidence. Retrieving exact indexed response.")
            return {
                "result": self.documents[best_idx]["response"],
                "thoughts": thoughts
            }

        # Synthesize response if match confidence is lower
        thoughts.append("Low confidence direct match. Synthesizing response using Markov chain generator.")
        synth_response = self._synthesize(query_tokens)
        
        # If synthesize fails to construct a meaningful response, fallback to best partial match
        if not synth_response and best_idx != -1:
            thoughts.append("Markov chain synthesis failed. Falling back to highest score partial match.")
            return {
                "result": self.documents[best_idx]["response"],
                "thoughts": thoughts
            }

        return {
            "result": synth_response or "I am still learning about that topic. Please teach me by typing: 'remember [fact]'.",
            "thoughts": thoughts
        }

    def _synthesize(self, seeds: list) -> str:
        """
        Generates a dynamic sentence using Markov transitions starting from query terms.
        """
        # Find a seed word that exists in the Markov model
        valid_seeds = [w for w in seeds if w in self.markov_model]
        if not valid_seeds:
            # Use random common word in our model
            valid_seeds = list(self.markov_model.keys())
            if not valid_seeds:
                return ""

        start_word = random.choice(valid_seeds)
        
        # Capitalize the start word or match its raw case from vocabulary
        current_word = start_word
        sentence = [current_word.capitalize()]
        
        max_length = 20
        for _ in range(max_length):
            next_options = self.markov_model.get(current_word.lower())
            if not next_options:
                break
            next_word = random.choice(next_options)
            sentence.append(next_word)
            current_word = next_word
            
            # Stop if we hit typical ending punctuation or logic
            if next_word.endswith(('.', '!', '?')):
                break

        res = " ".join(sentence)
        if not res.endswith(('.', '!', '?')):
            res += "."
        return res
