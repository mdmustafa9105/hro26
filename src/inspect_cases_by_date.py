import csv

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    import json
    outs = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

for r in reqs:
    cid = r["case_id"]
    steps = outs.get(cid, [])
    accs = [s["resource_id"] for s in steps if s["system_id"] == "account_service"]
    print(f"{cid} | req={r['requested_at']} | rep={r['reported_at']} | status={r['reported_status']} | audit={r['audit_at']} | accs={accs}")
