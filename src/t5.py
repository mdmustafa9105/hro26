import csv
data = []
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"]=="case_04":
            t = r["request_text"]
            print(repr(t))
            break
