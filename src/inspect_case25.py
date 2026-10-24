import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.identity import IdentityResolver
from src.parsers.unified_parser import UnifiedEvidenceParser

resolver = IdentityResolver("dataset")
identity_25 = resolver.resolve_by_email("s.yoon04@gmail.com")
print("Identity 25:", identity_25)

identity_26 = resolver.resolve_by_email("almeida.mariana@gmail.com")
print("Identity 26:", identity_26)

parser = UnifiedEvidenceParser("dataset")
records = parser.all_records

for r in records:
    if r.evidence_id == "evidence_92":
        if r.resource_id in ("account_3136", "account_5684", "audit_record_451", "audit_record_5416", "analytics_1895", "analytics_4566", "support_4715", "data_flow_6244", "backup_3120", "account_5334"):
            print(f"[{r.evidence_id}] {r.system_id} {r.resource_id} uid={r.user_id} email={r.email} phone={r.phone} hash={r.email_hash} details={r.raw_details}")
