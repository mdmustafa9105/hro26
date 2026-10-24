import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parsers.unified_parser import UnifiedEvidenceParser

parser = UnifiedEvidenceParser("dataset")
targets = ["audit_record_6645", "audit_record_5569", "audit_record_4902", "audit_record_4128", "audit_record_7095", "audit_record_3954", "audit_record_1707"]

for r in parser.all_records:
    if r.resource_id in targets:
        print(f"[{r.evidence_id} - cap={r.captured_at}] {r.system_id} {r.resource_id} user_id={r.user_id} email={r.email} subject_ref={r.subject_reference} details={r.raw_details}")
