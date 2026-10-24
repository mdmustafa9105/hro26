import csv

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in ("case_24", "case_25", "case_26", "case_27"):
            print(r)
