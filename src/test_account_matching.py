import csv
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.identity import IdentityResolver
from src.parsers.unified_parser import UnifiedEvidenceParser

def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

resolver = IdentityResolver("dataset")
parser = UnifiedEvidenceParser("dataset")

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    activities = list(csv.DictReader(f))

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    outs = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

# Build index of activities by resource
acts_by_res = {}
del_acts = []
for a in activities:
    res = a.get("resource_id", "")
    if res:
        acts_by_res.setdefault(res, []).append(a)
    if a.get("target_system") == "account_service" and a.get("event_type") == "DELETE_RECORD":
        del_acts.append(a)

print("Testing account matching...")
correct = 0
total = 0

for req in sample_reqs:
    cid = req["case_id"]
    steps = outs.get(cid, [])
    expected_accs = list(set([s["resource_id"] for s in steps if s["system_id"] == "account_service"]))
    if not expected_accs:
        continue
    expected_acc = expected_accs[0]
    total += 1

    identity = resolver.resolve_by_email(req["email"])
    user_records = parser.get_records_for_user(identity, req["audit_at"])

    rep_at = parse_iso(req["reported_at"])
    rep_status = req["reported_status"]
    exp_res = "SUCCESS" if rep_status == "COMPLETE" else ("PARTIAL" if rep_status == "PARTIALLY_COMPLETE" else "FAILED")

    # Candidate delete acts: within 90 minutes before reported_at with matching reported_result
    candidates = []
    for d in del_acts:
        d_time = parse_iso(d["event_time"])
        diff = (rep_at - d_time).total_seconds()
        if 0 <= diff <= 5400 and d["reported_result"] == exp_res:
            candidates.append((d, diff))

    # Score candidates based on user_records
    user_res_ids = {r.resource_id for r in user_records}
    scores = {}
    for d, diff in candidates:
        acc_id = d["resource_id"]
        d_time = parse_iso(d["event_time"])
        score = 0.0

        # Check direct user_records
        for ur in user_res_ids:
            for act in acts_by_res.get(ur, []):
                act_time = parse_iso(act["event_time"])
                if abs((act_time - d_time).total_seconds()) <= 3600:
                    score += 1000.0 - abs((act_time - d_time).total_seconds())

        # Proximity score to typical 50 min before reported_at (3000 sec)
        score += max(0, 3600 - abs(diff - 3000))
        scores[acc_id] = score

    if scores:
        best_acc = max(scores.items(), key=lambda x: x[1])[0]
    else:
        best_acc = None

    is_ok = (best_acc == expected_acc)
    if is_ok:
        correct += 1
    else:
        print(f"Mismatch {cid}: Expected={expected_acc} vs Got={best_acc} | candidates={[c[0]['resource_id'] for c in candidates]}")

print(f"Account resolution accuracy: {correct}/{total} ({correct/total:.2%})")
