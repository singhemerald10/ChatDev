from collections import deque, defaultdict
from typing import Deque, Dict, List, Optional

class CycleDetector:
    """
    Simple sliding-window cycle detector.
    Keeps last N actions per agent (strings). If a short sequence repeats back-to-back,
    detects a cycle and suggests a resolution.
    """
    def __init__(self, window: int = 12, min_cycle_len: int = 2):
        self.window = window
        self.min_cycle_len = min_cycle_len
        self.history: Dict[str, Deque[str]] = defaultdict(lambda: deque(maxlen=self.window))

    def add_action(self, agent_name: str, action_text: str) -> None:
        self.history[agent_name].append(action_text)

    def detect_cycle(self, agent_name: str) -> Optional[Dict]:
        """Return info dict if cycle detected, else None."""
        hist = list(self.history[agent_name])
        L = len(hist)
        # look for small repeated blocks like XYXY or AAAA
        for k in range(self.min_cycle_len, max(2, L // 2) + 1):
            last = hist[-k:]
            prev = hist[-2*k:-k] if L >= 2*k else None
            if prev and last == prev:
                return {"agent": agent_name, "cycle_len": k, "sequence": last}
        return None

    def resolve(self, agent_name: str) -> Dict:
        """
        Return a suggested remediation. Possible types:
         - reask: request the agent to re-evaluate and change approach
         - reassign: move task to different role
         - escalate: escalate to DTA
        """
        det = self.detect_cycle(agent_name)
        if not det:
            return {"action": "none"}
        # heuristic: short cycles -> reask, longer cycles -> reassign
        if det["cycle_len"] <= 3:
            return {"action": "reask", "reason": "short_repeating_loop"}
        return {"action": "reassign", "reason": "persistent_repetition"}