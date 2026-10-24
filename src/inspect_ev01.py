import csv

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["file_id"] == "evidence_01":
            print(r)
