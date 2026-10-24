from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any

@dataclass
class UserIdentity:
    user_id: str
    name: str
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    email_hashes: Set[str] = field(default_factory=set)
    names: Set[str] = field(default_factory=set)

    def matches(self, val: Optional[str]) -> bool:
        if not val:
            return False
        v_clean = val.strip().lower()
        if v_clean in self.emails or v_clean in self.email_hashes:
            return True
        v_orig = val.strip()
        if v_orig == self.user_id or v_orig in self.phones or v_orig in self.names:
            return True
        # Also check without plus or spaces for phones
        clean_phone = "".join(c for c in v_orig if c.isdigit())
        if clean_phone and len(clean_phone) >= 7:
            for p in self.phones:
                p_digits = "".join(c for c in p if c.isdigit())
                if clean_phone == p_digits:
                    return True
        return False

@dataclass
class EvidenceRecord:
    evidence_id: str
    file_path: str
    captured_at: str
    origin: str
    system_id: str
    resource_id: str
    data_category: str
    state: str  # PRESENT, ABSENT, REDACTED, ANONYMIZED, ACTIVE, DISABLED, BLOCKED
    user_id: Optional[str] = None
    customer_reference: Optional[str] = None
    subject_reference: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    email_hash: Optional[str] = None
    name: Optional[str] = None
    raw_details: Dict[str, Any] = field(default_factory=dict)

    def links_to_user(self, identity: UserIdentity) -> bool:
        for val in [self.user_id, self.customer_reference, self.subject_reference, 
                    self.email, self.phone, self.email_hash, self.name]:
            if identity.matches(val):
                return True
        # Recursively check raw details for any identifiers
        def check_val(v):
            if isinstance(v, str):
                return identity.matches(v)
            elif isinstance(v, dict):
                return any(check_val(sub_v) for sub_v in v.values())
            elif isinstance(v, (list, tuple, set)):
                return any(check_val(sub_v) for sub_v in v)
            return False

        return check_val(self.raw_details)

@dataclass
class AuditStep:
    step_no: int
    phase: str  # FINDING, REMEDIATION, VERIFICATION
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_no": self.step_no,
            "phase": self.phase,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "state": self.state,
            "evidence_id": self.evidence_id,
        }
