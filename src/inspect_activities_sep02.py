import csv

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for a in csv.DictReader(f):
        if a["event_time"].startswith("2026-09-02"):
            print(a["activity_id"], a["event_time"], a["source_system"], a["target_system"], a["event_type"], a["resource_id"], a["reported_result"], a["details"])
