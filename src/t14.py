from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data["sample_requests"]:
    if req["case_id"]=="case_04":
        t = req["request_text"]
        t2 = classification.is_deletion_request(t)
        print(t2)
        break
