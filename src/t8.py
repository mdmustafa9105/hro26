import csv
for r in csv.DictReader(open("dataset/sample_deletion_requests.csv",encoding="utf-8")):
    if r["case_id"]=="case_04":
        t = r["request_text"]
        # try all
        import re
        t2 = t
        t2 = t2.encode('utf-8', errors='ignore').decode('utf-8')
        # also do replacements
        t2 = t2.replace('\x92', "'") # cp1252
        t2 = t2.replace(chr(8217), "'")
        t2 = t2.replace(chr(0xFFFD), "'")
        t2 = t2.lower()
        print(t2)
        print("delet" in t2)
        break
