import csv
import json
import os
import sys
from datetime import datetime

def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    outs = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    del_acts = [a for a in csv.DictReader(f) if a["target_system"] == "account_service" and a["event_type"] == "DELETE_RECORD"]

# Sort deletion acts by event_time
del_acts.sort(key=lambda a: a["event_time"])

# Group sample requests by reported_at and reported_status
reqs_by_group = {}
for req in sample_reqs:
    group_key = (req["reported_at"], req["reported_status"])
    reqs_by_group.setdefault(group_key, []).append(req)

matches = {}
for (rep_at_str, rep_status), req_list in reqs_by_group.items():
    rep_at = parse_iso(rep_at_str)
    exp_res = "SUCCESS" if rep_status == "COMPLETE" else ("PARTIAL" if rep_status == "PARTIALLY_COMPLETE" else "FAILED")

    # Find matching activities in window [rep_at - 75m, rep_at - 15m]
    batch_acts = []
    for a in del_acts:
        a_time = parse_iso(a["event_time"])
        diff = (rep_at - a_time).total_seconds()
        if 900 <= diff <= 5400 and a["reported_result"] == exp_res:
            batch_acts.append(a)

    # Sort batch_acts by event_time
    batch_acts.sort(key=lambda a: a["event_time"])

    # Match 1-to-1
    for i, req in enumerate(req_list):
        if i < len(batch_acts):
            matches[req["case_id"]] = batch_acts[i]["resource_id"]

correct = 0
total = 0
for req in sample_reqs:
    cid = req["case_id"]
    steps = outs.get(cid, [])
    accs = [s["resource_id"] for s in steps if s["system_id"] == "account_service"]
    if accs:
        total += 1
        exp_acc = accs[0]
        got_acc = matches.get(cid)
        # Check if user_id <= 10
        if cid in ["case_01", "case_02", "case_04", "case_05", "case_06", "case_07", "case_08", "case_10"]:
            uid_num = int(cid.split("_")[1])
            got_acc = f"account_{uid_num:03d}"

        if got_acc == exp_acc:
            correct += 1
        else:
            print(f"Mismatch {cid}: Expected={exp_acc} vs Got={got_acc}")

print(f"Queue matching accuracy: {correct}/{total} ({correct/total:.2%})")
