import csv

accounts = [
    "account_3136", "account_3866", "account_5334", "account_5482", "account_5684", "account_6440",
    "account_410", "account_4990", "account_5037", "account_7012", "account_4163", "account_4857", "account_8858"
]

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for a in csv.DictReader(f):
        if a["resource_id"] in accounts:
            print(f"{a['resource_id']}: {a['event_time']} {a['source_system']} -> {a['target_system']} {a['event_type']} {a['reported_result']} details={a['details']}")
