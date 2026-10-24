from src.data import loader
from src.utils import classification
data = loader.load_all()
for req in data['sample_requests']:
    if req['case_id'] == 'case_04':
        print(classification.is_deletion_request(req['request_text']))
        break
