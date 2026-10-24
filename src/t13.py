from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data["sample_requests"]:
    if req["case_id"]=="case_04":
        t = req["request_text"]
        t2 = t.replace(chr(8217), "'").replace(chr(8216), "'")
        t2 = t2.replace("\u2019", "'").replace("\u2018", "'")
        t2 = t2.lower()
        print("delete" in t2)
        break
