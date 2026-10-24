import csv
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, '.')
from src.identity import IdentityResolver
from src.parsers.unified_parser import UnifiedEvidenceParser

resolver = IdentityResolver('dataset')
parser = UnifiedEvidenceParser('dataset')

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

# Test for each sample case: what resources are in golden vs what we can recover
for req in sample_requests:
    cid = req['case_id']
    email = req['email']
    audit_at = req['audit_at']
    rep_at = parse_iso(req['reported_at'])
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_res = set(s['resource_id'] for s in exp_steps)
    
    ident = resolver.resolve_by_email(email)
    user_recs = parser.get_records_for_user(ident, audit_at)
    rec_res = set(r.resource_id for r in user_recs)
    
    missing = exp_res - rec_res
    print(f"{cid} ({email}) - Exp: {len(exp_res)} Found: {len(rec_res)} Missing: {missing}")
