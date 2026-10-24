import csv
import json
import os
import sys

sys.path.insert(0, '.')
from src.parsers.unified_parser import UnifiedEvidenceParser

parser = UnifiedEvidenceParser('dataset')

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

# For each case, check which golden resources were found in evidence
for cid, r in golden.items():
    steps = json.loads(r['steps_json'])
    resources = {s['resource_id']: s['system_id'] for s in steps}
    
    print(f"\n{cid}: {len(resources)} resources: {list(resources.keys())}")
    for res_id, sys_id in resources.items():
        # Check in all evidence records
        matches = [rec for rec in parser.all_records if rec.resource_id == res_id]
        if matches:
            first = matches[0]
            print(f"  FOUND in evidence {first.evidence_id}: user={first.user_id} cust_ref={first.customer_reference} subj_ref={first.subject_reference} email={first.email}")
        else:
            print(f"  NOT in evidence: {res_id}")
