import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import DeletionAuditEngine

engine = DeletionAuditEngine("dataset")

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    import csv
    for r in csv.DictReader(f):
        if r["case_id"] == "case_25":
            req = r
            break

identity = engine.identity_resolver.resolve_by_email(req["email"])
user_records = engine.evidence_parser.get_records_for_user(identity, req["audit_at"])
account_id, account_ev_id = engine._resolve_account(identity, req, user_records)
print("Resolved account_id:", account_id, "account_ev_id:", account_ev_id)

acts = engine.acts_by_resource.get(account_id, [])
print(f"Activities for {account_id}:", len(acts))
for a in acts:
    print("  ", a)
