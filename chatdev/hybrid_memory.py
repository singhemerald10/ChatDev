import json
import os
from collections import deque
from typing import List, Dict, Any

def _tokenize(s: str):
    return set(s.lower().split())

class HybridMemory:
    """
    Lightweight hybrid memory:
    - short_term: deque of recent messages
    - long_term: list of dicts persisted to JSON with simple keyword retrieval
    """
    def __init__(self, storage_path: str, short_window: int = 50):
        self.storage_path = storage_path
        self.short_term = deque(maxlen=short_window)
        self.long_term: List[Dict[str, Any]] = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf8") as f:
                    self.long_term = json.load(f)
            except Exception:
                self.long_term = []

    def write(self, text: str, meta: Dict[str, Any] = None, persist: bool = False):
        entry = {"text": text, "meta": meta or {}, "tokens": list(_tokenize(text))}
        self.short_term.append(entry)
        if persist:
            self.long_term.append(entry)
            self._flush()

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        qtokens = _tokenize(query)
        scored = []
        # score long term
        for e in self.long_term:
            score = len(qtokens.intersection(set(e.get("tokens", []))))
            if score > 0:
                scored.append((score, e))
        # score short term
        for e in list(self.short_term):
            score = len(qtokens.intersection(set(e.get("tokens", []))))
            if score > 0:
                scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:k]]

    def _flush(self):
        try:
            with open(self.storage_path, "w", encoding="utf8") as f:
                json.dump(self.long_term, f, ensure_ascii=False, indent=2)
        except Exception:
            pass