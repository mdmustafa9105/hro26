import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cid = r["case_id"]
        if int(cid.split("_")[1]) >= 20:
            steps = json.loads(r["steps_json"])
            print(f"=== {cid}: {r['deletion_status']} ({len(steps)} steps) ===")
            for s in steps:
                print(f"  [{s['phase']}] {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} {s['evidence_id']}")
