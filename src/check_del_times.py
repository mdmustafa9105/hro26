import csv
import json
from datetime import datetime

def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    outs = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts_by_acc = {}
    for a in csv.DictReader(f):
        if a["target_system"] == "account_service" and a["event_type"] == "DELETE_RECORD":
            acts_by_acc[a["resource_id"]] = a

for r in sample_reqs:
    cid = r["case_id"]
    steps = outs.get(cid, [])
    accs = [s["resource_id"] for s in steps if s["system_id"] == "account_service"]
    if accs and accs[0] in acts_by_acc:
        act = acts_by_acc[accs[0]]
        diff_sec = (parse_iso(r["reported_at"]) - parse_iso(act["event_time"])).total_seconds()
        print(f"{cid} | acc={accs[0]} | rep_status={r['reported_status']} | act_res={act['reported_result']} | diff_sec={diff_sec:.0f}s ({diff_sec/60:.1f}m)")
