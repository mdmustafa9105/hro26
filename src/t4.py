import csv
from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data["sample_requests"]:
    if req["case_id"]=="case_04":
        t=req["request_text"]
        # replace
        t2 = t.replace(chr(8217), "'")
        print("delete" in t2.lower())
        print(classification.is_deletion_request(t))
        break
