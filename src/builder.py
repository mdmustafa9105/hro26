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

PHASE_ORDER = ['FINDING', 'REMEDIATION', 'VERIFICATION']

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
        # build maps
        self.resource_to_user = {}
        self.build_maps()
    
    def build_maps(self):
        for ef in self.data['evidence_files']:
            parsed = self.parser.parse(ef['file_id'])
            text = parsed['text'].lower()
            for ur in self.data['identities']:
                matched = False
                if ur['email'].lower() in text:
                    matched = True
                if ur['user_id'].lower() in text:
                    matched = True
                if ur['email_hash'].lower() in text:
                    matched = True
                if matched:
                    for r in parsed['resources']:
                        self.resource_to_user[r] = ur
    
    def find_resources_for_user(self, user_rows, audit_at):
        res_set = set()
        for ef in self.data['evidence_files']:
            cat = loader.parse_ts(ef['captured_at'])
            if audit_at and cat and cat > audit_at:
                continue
            parsed = self.parser.parse(ef['file_id'])
            text = parsed['text'].lower()
            for ur in user_rows:
                matched = False
                if ur['email'].lower() in text:
                    matched = True
                if ur['user_id'].lower() in text:
                    matched = True
                if ur['phone'] and ur['phone'].lower() in text:
                    matched = True
                if ur['email_hash'].lower() in text:
                    matched = True
                if matched:
                    for r in parsed['resources']:
                        res_set.add(r)
        # also from map
        for ur in user_rows:
            for rsrc, ruser in self.resource_to_user.items():
                if ruser['user_id'] == ur['user_id']:
                    res_set.add(rsrc)
        return res_set
    
    def find_evidence_for_resource_user(self, resource, user_rows):
        # find which evidence file proves relation
        for ef in self.data['evidence_files']:
            parsed = self.parser.parse(ef['file_id'])
            text = parsed['text'].lower()
            if resource in parsed['resources']:
                for ur in user_rows:
                    if ur['email'].lower() in text or ur['user_id'].lower() in text or ur['email_hash'].lower() in text:
                        return ef['file_id']
            # also if resource appears and user appears
            if resource in parsed['resources']:
                return ef['file_id']
        return None

def main():
    b = Builder()
    print('ok')
if __name__ == '__main__':
    main()