import json

path = "dataset/evidence/records/customer_data_snapshot_bundle_20260917.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for snap in data.get("snapshots", []):
    for rec in snap.get("records", []):
        if rec.get("resource_id") in ("analytics_1895", "analytics_4566", "analytics_5335", "analytics_4574", "analytics_6077", "account_3136", "account_5684", "account_6440", "account_3866", "account_5482"):
            print(snap.get("data_store"), rec)
