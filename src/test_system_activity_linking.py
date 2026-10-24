import csv
import json
from datetime import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    golden = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

with open('dataset/user_identities.csv', mode='r', encoding='utf-8') as f:
    email_to_uid = {r['email'].strip().lower(): r['user_id'].strip() for r in csv.DictReader(f)}

with open('dataset/user_audit_log.csv', mode='r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].strip().lower()] = r['user_id'].strip()
            email_to_uid[r['new_value'].strip().lower()] = r['user_id'].strip()

for req in sample_requests[:10]:
    c_id = req['case_id']
    uid = email_to_uid.get(req['email'].strip().lower())
    exp_steps = golden[c_id]
    exp_resources = set(s['resource_id'] for s in exp_steps)
    
    # Let's see: activities matching either user_id or within [requested_at, reported_at]
    req_at = parse_iso(req['requested_at'])
    rep_at = parse_iso(req['reported_at'])
    
    # candidate activities
    cand_res = set()
    for a in activities:
        a_time = parse_iso(a['event_time'])
        # if a mentions user_id
        if uid and uid in a['details']:
            cand_res.add(a['resource_id'])
        # or if close to reported_at (within 1 hour before reported_at)
        diff = (rep_at - a_time).total_seconds()
        if 0 <= diff <= 7200 and a['source_system'] == 'deletion_worker':
            cand_res.add(a['resource_id'])
            
    print(f"\n{c_id} ({uid}):")
    print(f"  Expected resources: {sorted(exp_resources)}")
    print(f"  Candidate resources: {sorted(cand_res)}")
    print(f"  Overlap: {sorted(exp_resources & cand_res)}")
