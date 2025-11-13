import os
import json
import time
import numpy as np
from typing import List, Dict, Any
from collections import deque
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class HybridMemory:
    """
    Hybrid Memory with semantic retrieval and metadata.
    - Short-term (deque) for recency
    - Long-term (JSON) for persistence
    - Semantic hybrid retrieval (keyword + vector similarity)
    """

    def __init__(self, storage_path: str, short_window: int = 50):
        self.storage_path = storage_path
        self.short_term = deque(maxlen=short_window)
        self.long_term: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        if os.path.exists(storage_path):
            try:
                with open(storage_path, "r", encoding="utf8") as f:
                    self.long_term = json.load(f)
            except Exception:
                self.long_term = []

    def write(self, text: str, meta: Dict[str, Any] = None, persist: bool = False):
        entry = {
            "text": text,
            "meta": meta or {},
            "timestamp": time.time(),
        }
        entry["meta"].setdefault("tokens", text.lower().split())
        self.short_term.append(entry)
        if persist:
            self.long_term.append(entry)
            self._flush()

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not (self.long_term or self.short_term):
            return []

        corpus = [e["text"] for e in list(self.short_term) + self.long_term]
        try:
            vectors = self.vectorizer.fit_transform(corpus + [query])
            sims = cosine_similarity(vectors[-1], vectors[:-1])[0]
            idxs = np.argsort(-sims)[:k]
            combined = list(self.short_term) + self.long_term
            return [
                {
                    "score": float(sims[i]),
                    "text": combined[i]["text"],
                    "meta": combined[i]["meta"],
                }
                for i in idxs
                if sims[i] > 0
            ]
        except Exception:
            return []

    def prune(self, max_size: int = 500):
        """Keep only the most recent N items."""
        if len(self.long_term) > max_size:
            self.long_term = self.long_term[-max_size:]
            self._flush()

    def _flush(self):
        try:
            with open(self.storage_path, "w", encoding="utf8") as f:
                json.dump(self.long_term, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
