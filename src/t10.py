from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data["sample_requests"]:
    if req["case_id"]=="case_04":
        t = req["request_text"]
        t2 = str(t)
        try:
            t2 = t2.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception:
            pass
        t2 = t2.replace(chr(8217), "'").replace(chr(8216), "'")
        t2 = t2.replace(chr(0xFFFD), "'").replace(chr(0x92), "'")
        t2 = t2.lower()
        print("delete" in t2)
        break
