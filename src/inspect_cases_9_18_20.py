import csv
import json

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_outs = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    users = {r["email"]: r for r in csv.DictReader(f)}

for cid in ["case_09", "case_18", "case_20"]:
    req = sample_reqs[cid]
    u = users.get(req["email"])
    steps = sample_outs.get(cid, [])
    aud_step = [s for s in steps if s["system_id"] == "security_service"]
    print(f"{cid} | email={req['email']} | user_id={u.get('user_id') if u else 'N/A'} | expected audit={aud_step}")
