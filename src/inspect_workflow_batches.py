import csv

dates = ["2026-08-27", "2026-08-30", "2026-09-01", "2026-09-02", "2026-09-05", "2026-09-06", "2026-09-09"]

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for a in csv.DictReader(f):
        t = a["event_time"][:10]
        if t in dates and (a["source_system"] == "deletion_worker" or "Policy action" in a["details"]):
            print(f"{a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']} | {a['details']}")
