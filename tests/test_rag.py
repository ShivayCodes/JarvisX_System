import numpy as np

from jarvis_x.ai.rag import SemanticRAG


class FakeEncoder:
    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False, batch_size=32):
        vectors = []
        for text in texts:
            value = float(sum(ord(ch) for ch in text) % 1000)
            vectors.append([value + 1.0, len(text) + 1.0])
        vectors = np.asarray(vectors, dtype=np.float32)
        if normalize_embeddings:
            vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors


def test_rag_add_deduplicates_and_round_trips(tmp_path):
    rag = SemanticRAG()
    rag.model = FakeEncoder()
    rag.index_path = tmp_path / "rag.json"

    added = rag.add([
        {"text": "Python is a programming language.", "source": "test"},
        {"text": "Python is a programming language.", "source": "test"},
    ])
    assert added == 1
    rag.save()

    loaded = SemanticRAG()
    loaded.model = FakeEncoder()
    loaded.index_path = rag.index_path
    assert loaded.load()
    results = loaded.search("Python programming", top_k=1)
    assert results
    assert results[0]["source"] == "test"
