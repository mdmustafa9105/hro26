import csv
for r in csv.DictReader(open("dataset/sample_deletion_requests.csv",encoding="utf-8")):
    if r["case_id"]=="case_04":
        t = r["request_text"]
        t2 = str(t)
        t2 = t2.replace(chr(8217), "'").replace(chr(8216), "'")
        t2 = t2.replace(chr(0xFFFD), "'")
        t2 = t2.lower()
        print(t2)
        print("delete" in t2)
        break
