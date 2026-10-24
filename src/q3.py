import csv
for r in csv.DictReader(open("dataset/sample_deletion_requests.csv",encoding="utf-8")):
    if r["case_id"]=="case_04":
        t=r["request_text"]
        break
# replace smart apostrophe
t2 = t
# try
t2 = t.replace(chr(8217), "'")
print("delete" in t2.lower())
