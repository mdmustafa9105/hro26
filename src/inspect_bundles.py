import csv

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if "customer_data_snapshot_bundle" in r["file_path"]:
            print(r)
