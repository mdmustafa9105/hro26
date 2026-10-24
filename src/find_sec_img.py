import csv

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if "security_audit_explorer" in r["file_path"]:
            print(r)
