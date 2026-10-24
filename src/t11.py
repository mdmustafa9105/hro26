from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data["sample_requests"]:
    if req["case_id"]=="case_04":
        t = req["request_text"]
        print(type(t))
        print(t)
        break
