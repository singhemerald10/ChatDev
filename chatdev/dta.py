import time
from typing import Dict
from chatdev.utils import log_visualize


class DynamicTerminationAgent:
    """
    Dynamic Termination Agent (DTA)
    Monitors execution and decides whether to stop based on:
      - Total step count (max_steps)
      - Idle duration (idle_threshold_sec)
      - Repeated cycles (cycle_limit)
    """

    def __init__(self, max_steps: int = 500, idle_threshold_sec: int = 300, cycle_limit: int = 3):
        self.max_steps = max_steps
        self.idle_threshold_sec = idle_threshold_sec
        self.cycle_limit = cycle_limit

        # internal trackers
        self.step_count = 0
        self.last_progress_ts = time.time()
        self.cycle_hits: Dict[str, int] = {}

    def maybe_terminate(self, chat_env, cycle_detector) -> Dict:
        """
        Evaluate termination conditions using environment state.

        Args:
            chat_env: Current ChatEnv instance.
            cycle_detector: Instance of CycleDetector.

        Returns:
            dict: {"terminate": bool, "reason": str}
        """
        self.step_count += 1

        # --- 1. Step limit ---
        if self.step_count >= self.max_steps:
            return {"terminate": True, "reason": f"Exceeded max steps ({self.max_steps})"}

        # --- 2. Idle timeout ---
        now = time.time()
        idle_for = now - self.last_progress_ts
        if idle_for > self.idle_threshold_sec:
            return {"terminate": True, "reason": f"Idle timeout ({int(idle_for)}s)"}

        # --- 3. Detect persistent cycles ---
        if hasattr(chat_env, "last_actions"):
            for agent, action in chat_env.last_actions.items():
                if not action:
                    continue
                det = cycle_detector.detect_cycle(agent)
                if det:
                    self.cycle_hits[agent] = self.cycle_hits.get(agent, 0) + 1
                    log_visualize(f"[DTA] Detected cycle for {agent} ({self.cycle_hits[agent]}/{self.cycle_limit})")
                    if self.cycle_hits[agent] >= self.cycle_limit:
                        return {"terminate": True, "reason": f"Repeated cycles for {agent}"}

        # --- 4. Update last progress timestamp ---
        if getattr(chat_env, "last_actions", {}):
            self.last_progress_ts = now

        return {"terminate": False, "reason": "continue"}
