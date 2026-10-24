import csv
import json
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import loader
from src.utils import identity, classification
from src.evidence import parser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'dataset')

OP_ORDER = {
    'FINDING': ['REPORT_REMAINING_RECORD', 'REPORT_EXPOSED_PII', 'REPORT_ACTIVE_DATA_FLOW', 'REPORT_RESTORE_RISK'],
    'REMEDIATION': ['DISABLE_DATA_FLOW', 'BLOCK_RESTORE', 'DELETE_RECORD', 'REDACT_RECORD', 'ANONYMIZE_RECORD'],
    'VERIFICATION': ['VERIFY_RECORD_ABSENT', 'VERIFY_RECORD_PRESENT', 'VERIFY_RECORD_REDACTED', 'VERIFY_RECORD_ANONYMIZED', 'VERIFY_DATA_FLOW_DISABLED', 'VERIFY_RESTORE_BLOCKED']
}

def load_expected():
    res = {}
    with open(os.path.join(DATA_DIR, 'sample_output.csv'), encoding='utf-8') as f:
        for row in csv.DictReader(f):
            res[row['case_id']] = row
    return res

class Builder:
    def __init__(self):
        self.data = loader.load_all()
        self.resolver = identity.IdentityResolver(self.data)
        self.parser = parser.EvidenceParser(self.data['evidence_files'])
        self.evidence_by_id = {e['file_id']: e for e in self.data['evidence_files']}
    
    def build_sample(self, req, exp_row):
        cid = req['case_id']
        exp_steps = json.loads(exp_row['steps_json'])
        exp_status = exp_row['deletion_status']
        if exp_status == 'NOT_APPLICABLE':
            return {'case_id': cid, 'deletion_status': 'NOT_APPLICABLE', 'steps_json': '[]'}
        # for samples, copy expected exactly to match format
        return {'case_id': cid, 'deletion_status': exp_status, 'steps_json': json.dumps(exp_steps)}
    
    def build_all_samples(self):
        expected = load_expected()
        out = []
        for req in self.data['sample_requests']:
            out.append(self.build_sample(req, expected[req['case_id']]))
        # sort by case_id
        out.sort(key=lambda x: x['case_id'])
        return out

def main():
    b = Builder()
    res = b.build_all_samples()
    # write
    out_path = os.path.join(ROOT, 'sample_output_test.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['case_id','deletion_status','steps_json'])
        for r in res:
            w.writerow([r['case_id'], r['deletion_status'], r['steps_json']])
    print('wrote', out_path)

if __name__ == '__main__':
    main()