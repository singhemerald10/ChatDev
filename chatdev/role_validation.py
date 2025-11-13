import re
import json
import logging
import unicodedata
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class RoleValidator:
    """
    Dual-Constraint Role Validator (Research-Ready)
    - Normalizes text for robust regex matching
    - Applies deny > allow precedence
    - Supports dynamic overrides
    - Logs structured JSON decisions for reproducibility
    """

    def __init__(
        self,
        role_constraints: Dict[str, Dict[str, List[str]]],
        log_file: str = "role_validation_log.jsonl",
    ):
        self.constraints = {}
        self.log_file = log_file
        self.logger = logging.getLogger("RoleValidator")
        self.overrides = {"allow": [], "deny": []}

        for role, rules in (role_constraints or {}).items():
            self.constraints[role] = {
                "allow": [re.compile(p, re.I) for p in rules.get("allow", [])],
                "deny": [re.compile(p, re.I) for p in rules.get("deny", [])],
            }

    # ---------- internal helpers ----------
    def _normalize(self, text: str) -> str:
        """Case-fold, remove punctuation/extra spaces."""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"[^\w\s]", " ", text).lower()
        return re.sub(r"\s+", " ", text.strip())

    def _log(self, record: dict):
        record["timestamp"] = datetime.utcnow().isoformat()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    # ---------- core ----------
    def validate_action(self, role: str, text: str) -> Tuple[bool, str, dict]:
        norm = self._normalize(text)
        c = self.constraints.get(role)
        details = {"role": role, "text": norm}

        # unknown role
        if not c:
            details["decision"] = "no_constraints"
            return True, "no_constraints", details

        # overrides first
        for pat in self.overrides["deny"]:
            if pat.search(norm):
                details.update({"decision": "deny_override", "pattern": pat.pattern})
                return False, f"override_deny:{pat.pattern}", details

        for pat in c["deny"]:
            if pat.search(norm):
                details.update({"decision": "deny", "pattern": pat.pattern})
                return False, f"forbidden_pattern:{pat.pattern}", details

        for pat in self.overrides["allow"]:
            if pat.search(norm):
                details.update({"decision": "allow_override", "pattern": pat.pattern})
                return True, "allow_override", details

        if c["allow"]:
            for pat in c["allow"]:
                if pat.search(norm):
                    details.update({"decision": "allow", "pattern": pat.pattern})
                    return True, "allowed", details
            details["decision"] = "no_allow_match"
            return False, "no_allow_pattern", details

        details["decision"] = "allowed_by_default"
        return True, "allowed_by_default", details

    def enforce(self, role: str, text: str) -> Tuple[bool, dict]:
        ok, reason, details = self.validate_action(role, text)
        suggestion = "proceed" if ok else "rephrase_or_reassign"
        record = {
            "ok": ok,
            "role": role,
            "reason": reason,
            "suggestion": suggestion,
            "details": details,
        }
        self._log(record)
        return ok, record

    def add_override(self, rule_type: str, pattern: str):
        if rule_type not in ("allow", "deny"):
            raise ValueError("rule_type must be 'allow' or 'deny'")
        self.overrides[rule_type].append(re.compile(pattern, re.I))
