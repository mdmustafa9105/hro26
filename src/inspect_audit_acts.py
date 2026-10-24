import csv

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for a in csv.DictReader(f):
        if a["resource_id"] in ["audit_record_4902", "audit_record_6645", "audit_record_5569", "audit_record_4128", "audit_record_7095", "audit_record_3954", "audit_record_1707"]:
            print(a)
