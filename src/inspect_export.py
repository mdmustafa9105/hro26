import json

path = "dataset/evidence/records/service_resource_export_20260915_114455.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

terms = ["account_3136", "account_5684", "analytics_1895", "analytics_4566", "account_5334"]

def search_obj(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(t in str(k) or t in str(v) for t in terms):
                print(f"Match at {prefix}.{k}: {v}")
            else:
                search_obj(v, f"{prefix}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if any(t in str(item) for t in terms):
                print(f"Match at {prefix}[{i}]: {item}")
            else:
                search_obj(item, f"{prefix}[{i}]")

search_obj(data)
