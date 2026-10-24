import json

with open("dataset/evidence/records/customer_data_snapshot_bundle_20261014.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for snap in data.get("snapshots", []):
    for rec in snap.get("records", []):
        if rec.get("resource_id") == "analytics_9914":
            print(snap.get("data_store"), rec)
