from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from jarvis_x.core.config import Config


class SemanticRAG:
    """Lightweight local vector index backed by Sentence Transformers + NumPy."""

    def __init__(self, model_id: str | None = None):
        self.model_id = model_id or Config.EMBEDDING_MODEL_ID
        self.model = None
        self.documents: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self.index_path = Path(Config.RAG_INDEX_PATH)

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_id)

    def add(self, documents: Iterable[dict]) -> int:
        docs = [dict(d) for d in documents if d.get("text")]
        if not docs:
            return 0
        self._load_model()
        vectors = self.model.encode(
            [d["text"] for d in docs],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        vectors = np.asarray(vectors, dtype=np.float32)
        if self.embeddings is None:
            self.embeddings = vectors
        else:
            self.embeddings = np.vstack([self.embeddings, vectors])
        self.documents.extend(docs)
        return len(docs)

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        if not query.strip() or self.embeddings is None or not self.documents:
            return []
        self._load_model()
        q = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        scores = self.embeddings @ np.asarray(q[0], dtype=np.float32)
        ids = np.argsort(scores)[::-1][:top_k]
        return [
            {**self.documents[i], "score": float(scores[i])}
            for i in ids
            if float(scores[i]) >= Config.RAG_MIN_SCORE
        ]

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self.index_path.with_suffix(".npy"), self.embeddings)
        self.index_path.write_text(json.dumps(self.documents, ensure_ascii=False), encoding="utf-8")

    def load(self) -> bool:
        try:
            meta = json.loads(self.index_path.read_text(encoding="utf-8"))
            vectors = np.load(self.index_path.with_suffix(".npy"))
            if len(meta) != len(vectors):
                return False
            self.documents = meta
            self.embeddings = vectors.astype(np.float32)
            return True
        except (OSError, ValueError, json.JSONDecodeError):
            return False
