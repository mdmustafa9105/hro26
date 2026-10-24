import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.identity import IdentityResolver
from src.parsers.unified_parser import UnifiedEvidenceParser

resolver = IdentityResolver("dataset")
identity = resolver.resolve_by_email("s.yoon04@gmail.com")
print("Identity:", identity)

parser = UnifiedEvidenceParser("dataset")
recs = parser.get_records_for_user(identity, "2026-09-15T12:00:00Z")
print(f"Total user records for case_25: {len(recs)}")
for r in recs:
    print(r.evidence_id, r.system_id, r.resource_id, r.state, r.user_id, r.raw_details.get("subject_reference"))
