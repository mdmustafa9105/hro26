import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import loader
from src.utils import identity, classification

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'dataset')

def load_expected():
    path = os.path.join(DATA_DIR, 'sample_output.csv')
    res = {}
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            res[row['case_id']] = row
    return res

def classify_request(req, resolver):
    text = req.get('request_text','')
    if not classification.is_deletion_request(text):
        return 'NOT_APPLICABLE', []
    # for now, do basic resolution
    email = req.get('email','')
    matches = resolver.resolve(email)
    if not matches:
        # try to find any match? maybe still treat as deletion request but no identity found - but problem states cases are requests
        # default to incomplete if deletion requested but can't fully resolve? not sure; follow samples
        pass
    # naive: look up sample behavior - but we need to infer; start simple
    return None, None  # placeholder

def main():
    data = loader.load_all()
    resolver = identity.IdentityResolver(data)
    expected = load_expected()
    # test on samples first pass
    for req in data['sample_requests']:
        cid = req['case_id']
        email = req['email']
        text = req['request_text']
        is_del = classification.is_deletion_request(text)
        matches = resolver.resolve(email)
        ids = set()
        for m in matches:
            ids |= resolver.get_identifiers(m)
        exp = expected[cid]
        print(cid, email, is_del, len(matches), exp['deletion_status'])

if __name__ == '__main__':
    main()
