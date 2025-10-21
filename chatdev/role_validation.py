import re
from typing import Dict, List, Tuple

class RoleValidator:
    """
    Dual-Constraint role validator.
    role_constraints format:
      {
        "RoleName": {
            "allow": ["allowed phrase regex", ...],
            "deny": ["forbidden phrase regex", ...]
        },
        ...
      }
    """
    def __init__(self, role_constraints: Dict[str, Dict[str, List[str]]]):
        # normalize regex lists
        self.constraints = {}
        for r, c in (role_constraints or {}).items():
            self.constraints[r] = {
                "allow": [re.compile(pat, re.I) for pat in c.get("allow", [])],
                "deny": [re.compile(pat, re.I) for pat in c.get("deny", [])]
            }

    def validate_action(self, role_name: str, action_text: str) -> Tuple[bool, str]:
        """Return (ok, reason). If not ok, reason explains violation."""
        c = self.constraints.get(role_name)
        if not c:
            return True, "no_constraints"
        # Deny checks first
        for pat in c["deny"]:
            if pat.search(action_text):
                return False, f"forbidden_pattern_matched: {pat.pattern}"
        # If allow list exists, require at least one match
        if c["allow"]:
            for pat in c["allow"]:
                if pat.search(action_text):
                    return True, "allowed"
            return False, "no_allow_pattern_matched"
        return True, "allowed_by_default"

    def enforce(self, role_name: str, action_text: str) -> Tuple[bool, str]:
        """
        Enforce rules. Returns (ok, suggestion_or_reason).
        If not ok, suggestion_or_reason contains a short guidance like 're-prompt' or 'reassign'.
        """
        ok, reason = self.validate_action(role_name, action_text)
        if ok:
            return True, "ok"
        # Simple enforcement strategy: re-prompt to stay in role
        if reason.startswith("forbidden_pattern"):
            return False, "please_rephrase_to_avoid_forbidden_behavior"
        if reason == "no_allow_pattern_matched":
            return False, "please_focus_on_role_responsibilities"
        return False, reason
