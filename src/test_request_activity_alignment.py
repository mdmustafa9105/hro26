import csv
from datetime import datetime, timezone
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    del_acts = [r for r in csv.DictReader(f) if r['source_system'] == 'deletion_worker' and r['event_type'] == 'DELETE_RECORD' and r['target_system'] == 'account_service']

for req in sample_requests[:15]:
    c_id = req['case_id']
    rep_at = parse_iso(req['reported_at'])
    
    # find closest DELETE_RECORD on account_service
    closest = None
    min_diff = 999999999
    for a in del_acts:
        a_time = parse_iso(a['event_time'])
        diff = abs((a_time - rep_at).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest = a
            
    print(f"{c_id} (rep_at: {req['reported_at']}): closest account={closest['resource_id']} diff={min_diff:.0f}s ({closest['reported_result']})")
