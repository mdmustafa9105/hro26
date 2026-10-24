import sys
sys.path.insert(0, ".")
from pathlib import Path
from src.parsers.unified_parser import UnifiedEvidenceParser
from src.identity import IdentityResolver

dataset_dir = Path("dataset")
p = UnifiedEvidenceParser(dataset_dir)
resolver = IdentityResolver(dataset_dir)

for r in p.all_records:
    if "6645" in r.resource_id or "5569" in r.resource_id:
        print(f"Record: {r.system_id} | {r.resource_id} | user_id={r.user_id} | email={r.email} | hash={r.email_hash} | evidence={r.evidence_id}")

import csv
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["case_id"] in ("case_19", "case_20"):
            print(row)
            identity = resolver.resolve_by_email(row["email"])
            print("Resolved identity:", identity)

