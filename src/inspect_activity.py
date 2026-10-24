import csv
import json

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("Fieldnames:", reader.fieldnames)
    rows = list(reader)
    print(f"Total rows: {len(rows)}")
    for r in rows[:10]:
        print(r)
