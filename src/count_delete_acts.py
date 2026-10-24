import csv

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    del_acts = [a for a in csv.DictReader(f) if a["target_system"] == "account_service" and a["event_type"] == "DELETE_RECORD"]

print("Total DELETE_RECORD account_service acts:", len(del_acts))
