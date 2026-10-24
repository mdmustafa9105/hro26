import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parsers.unified_parser import UnifiedEvidenceParser

parser = UnifiedEvidenceParser("dataset")

for r in parser.all_records:
    if r.system_id == "security_service":
        for u in ["user_61", "user_50", "user_48"]:
            if u in str(r.user_id) or u in str(r.subject_reference) or u in str(r.customer_reference) or u in str(r.raw_details):
                print(f"[{r.evidence_id} - {r.captured_at}] {r.resource_id} matches {u}")
