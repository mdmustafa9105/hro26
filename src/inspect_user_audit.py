import csv

with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("user_audit_log fieldnames:", reader.fieldnames)
    rows = list(reader)
    print("total rows:", len(rows))
    for r in rows[:10]:
        print(r)
