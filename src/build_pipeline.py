import csv
import json
import os
import sys

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

class Pipeline:
    def __init__(self):
        self.data = loader.load_all()
        self.resolver = identity.IdentityResolver(self.data)
        self.parser = parser.EvidenceParser(self.data['evidence_files'])
        self.rules = {r['data_category']: r for r in self.data['rules']}
        self.evidence_by_id = {e['file_id']: e for e in self.data['evidence_files']}
        self.activity = self.data['activity']
    
    def process_case(self, req):
        cid = req['case_id']
        text = req['request_text']
        if not classification.is_deletion_request(text):
            return {'case_id': cid, 'deletion_status': 'NOT_APPLICABLE', 'steps_json': '[]'}
        email = req['email']
        matches = self.resolver.resolve(email)
        if not matches:
            return {'case_id': cid, 'deletion_status': 'INCOMPLETE', 'steps_json': '[]'}  # will fix
        # collect all identifiers
        all_ids = set()
        user_rows = []
        for m in matches:
            user_rows.append(m)
            all_ids |= self.resolver.get_identifiers(m)
        # get audit_at
        audit_at = loader.parse_ts(req['audit_at'])
        # find relevant evidence files (all for now, filter by captured_at)
        candidate_evidence = []
        for ef in self.data['evidence_files']:
            cat = loader.parse_ts(ef['captured_at'])
            if audit_at and cat and cat > audit_at:
                continue
            candidate_evidence.append(ef['file_id'])
        # parse candidates and see which mention our resources/idents
        relevant_evidence = []
        for efid in candidate_evidence:
            parsed = self.parser.parse(efid)
            # check match
            hit = False
            # check emails
            for e in parsed.get('emails', []):
                if e in all_ids:
                    hit = True
                    break
            if hit:
                relevant_evidence.append((efid, parsed))
                continue
            # check resources mentioned - if resource belongs to subject? hard to tell; but include if seen in context of subject
            # for samples, easier to be inclusive if mentions account related to user? maybe check by trying to find mapping
            relevant_evidence.append((efid, parsed))  # be broad for now
        # try to find specific resources for this user
        subject_resources = set()
        for ur in user_rows:
            # look in parsed evidence for resources that appear near user's identifiers
            for efid, parsed in relevant_evidence:
                # if user email/hash/phone in text, collect resources in same parsed
                text_all = parsed['text'].lower()
                matched_user = False
                if ur.get('email') and ur['email'].lower() in text_all:
                    matched_user = True
                if ur.get('user_id') and ur['user_id'] in text_all:
                    matched_user = True
                if ur.get('email_hash') and ur['email_hash'].lower() in text_all:
                    matched_user = True
                if matched_user:
                    for r in parsed['resources']:
                        subject_resources.add(r)
        return {'case_id': cid, 'deletion_status': 'UNKNOWN', 'subject_resources': list(subject_resources), 'relevant_evidence': [e[0] for e in relevant_evidence], 'user_rows': user_rows}

def main():
    p = Pipeline()
    data = loader.load_all()
    expected = load_expected()
    for req in data['sample_requests'][:3]:
        res = p.process_case(req)
        print(req['case_id'], res.get('deletion_status'), res.get('subject_resources')[:10])

if __name__ == '__main__':
    main()