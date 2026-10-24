import csv
for r in csv.DictReader(open("dataset/sample_deletion_requests.csv",encoding="utf-8")):
    if r["case_id"]=="case_04":
        t=r["request_text"]
        break
# in the file as read, check
print(type(t))
for i,c in enumerate(t):
    if ord(c)>127:
        print(i, hex(ord(c)), c)
        break
