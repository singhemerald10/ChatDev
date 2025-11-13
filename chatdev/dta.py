import time
from typing import Dict
import json
from datetime import datetime

class DynamicTerminationAgent:
    """
    Dynamic Termination Agent (research-ready)
    Evaluates step, idle, and semantic cycle criteria with graded responses.
    """

    def __init__(
        self,
        max_steps: int = 500,
        idle_threshold_sec: int = 300,
        cycle_limit: int = 3,
        log_file: str = "termination_log.jsonl"
    ):
        self.max_steps = max_steps
        self.idle_threshold_sec = idle_threshold_sec
        self.cycle_limit = cycle_limit
        self.step_count = 0
        self.last_progress_ts = time.time()
        self.cycle_hits: Dict[str, int] = {}
        self.log_file = log_file

    def _log(self, record: dict):
        record["timestamp"] = datetime.utcnow().isoformat()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def maybe_terminate(self, chat_env, context: Dict) -> Dict:
        self.step_count += 1
        now = time.time()
        idle_for = now - self.last_progress_ts
        record = {"step": self.step_count}

        # Step limit
        if self.step_count >= self.max_steps:
            record.update({"terminate": True, "reason": "max_steps"})
            self._log(record)
            return record

        # Idle timeout
        if idle_for > self.idle_threshold_sec:
            record.update({"terminate": True, "reason": f"idle_{int(idle_for)}s"})
            self._log(record)
            return record

        # Cycle checks
        cycle_detector = context.get("cycle_detector")
        if hasattr(chat_env, "last_actions"):
            for agent, _ in chat_env.last_actions.items():
                det = cycle_detector.detect_cycle(agent) if cycle_detector else None
                if det:
                    self.cycle_hits[agent] = self.cycle_hits.get(agent, 0) + 1
                    if self.cycle_hits[agent] >= self.cycle_limit:
                        record.update({
                            "terminate": True,
                            "reason": f"persistent_cycles_{agent}",
                            "hits": self.cycle_hits[agent],
                        })
                        self._log(record)
                        return record

        # success condition hook (optional)
        if getattr(chat_env, "task_success", False):
            record.update({"terminate": True, "reason": "success"})
            self._log(record)
            return record

        # progress
        if getattr(chat_env, "last_actions", {}):
            self.last_progress_ts = now

        record.update({"terminate": False, "reason": "continue"})
        self._log(record)
        return record
