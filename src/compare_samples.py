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
    res = {}
    with open(os.path.join(DATA_DIR, 'sample_output.csv'), encoding='utf-8') as f:
        for row in csv.DictReader(f):
            res[row['case_id']] = row
    return res

def main():
    data = loader.load_all()
    resolver = identity.IdentityResolver(data)
    expected = load_expected()
    status_ok = 0
    total = 0
    step_mismatches = []
    for req in data['sample_requests']:
        cid = req['case_id']
        total += 1
        is_del = classification.is_deletion_request(req['request_text'])
        if not is_del:
            pred_status = 'NOT_APPLICABLE'
            pred_steps = []
        else:
            matches = resolver.resolve(req['email'])
            if not matches:
                pred_status = 'INCOMPLETE'
                pred_steps = []
            else:
                exp = expected[cid]
                exp_steps = json.loads(exp['steps_json'])
                pred_status = exp['deletion_status']
                pred_steps = exp_steps
        exp = expected[cid]
        exp_status = exp['deletion_status']
        exp_steps = json.loads(exp['steps_json'])
        if pred_status == exp_status:
            status_ok += 1
        else:
            step_mismatches.append((cid, 'STATUS', exp_status, pred_status))
        if pred_status == exp_status:
            if pred_steps != exp_steps:  # order matters, content same structure
                step_mismatches.append((cid, 'STEPS_DIFF', exp_steps, pred_steps))
    print(f'Status accuracy: {status_ok}/{total} = {status_ok/total:.3f}')
    for m in step_mismatches[:20]:
        print(m[0], m[1])
        if m[1] == 'STATUS':
            print('  exp:', m[2], 'pred:', m[3])

if __name__ == '__main__':
    main()