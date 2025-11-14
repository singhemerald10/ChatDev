import re
import math
import numpy as np
from collections import deque, defaultdict
from typing import Deque, Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CycleDetector:
    """
    Semantic Cycle Detector (research-ready)
    Detects repetitive loops by text similarity and sequence patterns.
    """

    def __init__(self, window: int = 12, min_cycle_len: int = 2, sim_threshold: float = 0.85):
        self.window = window
        self.min_cycle_len = min_cycle_len
        self.sim_threshold = sim_threshold
        self.history: Dict[str, Deque[str]] = defaultdict(lambda: deque(maxlen=self.window))
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def add_action(self, agent: str, text: str):
        self.history[agent].append(self._normalize(text))

    def _normalize(self, s: str) -> str:
        s = re.sub(r"[^\w\s]", " ", s.lower())
        return re.sub(r"\s+", " ", s.strip())

    def detect_cycle(self, agent: str) -> Optional[Dict]:
        hist = list(self.history[agent])
        if len(hist) < 2 * self.min_cycle_len:
            return None

        # pattern repetition (literal)
        for k in range(self.min_cycle_len, len(hist)//2 + 1):
            if hist[-k:] == hist[-2*k:-k]:
                return {"agent": agent, "cycle_len": k, "sequence": hist[-k:], "confidence": 1.0}

        # semantic similarity check
        try:
            vectors = self.vectorizer.fit_transform(hist[-self.min_cycle_len*2:])
            sims = cosine_similarity(vectors[-1], vectors[:-1])[0]
            max_sim = float(np.max(sims)) if sims.size else 0.0
            if max_sim >= self.sim_threshold:
                return {
                    "agent": agent,
                    "cycle_len": 1,
                    "sequence": [hist[-1]],
                    "confidence": max_sim,
                }
        except Exception:
            pass
        return None

    def resolve(self, agent: str) -> Dict:
        det = self.detect_cycle(agent)
        if not det:
            return {"action": "none"}
        conf = det.get("confidence", 0)
        if det["cycle_len"] <= 3 and conf < 0.95:
            return {"action": "reask", "reason": "short_or_low_confidence"}
        elif conf >= 0.95:
            return {"action": "reassign", "reason": "persistent_high_confidence"}
        return {"action": "escalate", "reason": "uncertain_pattern"}
