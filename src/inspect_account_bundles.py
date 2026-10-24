import glob
import json

bundle_files = glob.glob("dataset/evidence/records/customer_data_snapshot_bundle_*.json")
print(f"Found {len(bundle_files)} snapshot bundles.")

account_user_map = {}

for bf in bundle_files:
    with open(bf, "r", encoding="utf-8") as f:
        data = json.load(f)
    for snap in data.get("snapshots", []):
        if snap.get("data_store") == "account_service":
            for rec in snap.get("records", []):
                acc_id = rec.get("resource_id")
                cust_ref = rec.get("customer_reference")
                email = rec.get("email")
                if acc_id:
                    account_user_map[acc_id] = (cust_ref, email, bf)

print(f"Total unique account_service mappings in snapshot bundles: {len(account_user_map)}")
sample_terms = ["account_3136", "account_3866", "account_5334", "account_5482", "account_5684", "account_6440", "account_410", "account_4990", "account_5037", "account_7012", "account_4163", "account_4857", "account_8858"]
for st in sample_terms:
    print(f"  {st}: {account_user_map.get(st)}")
