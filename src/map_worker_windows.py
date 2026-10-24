import csv

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# Look at activities where source_system == 'deletion_worker' or event_type == 'DELETE_RECORD'
# Let's see: for each sample request, what deletion_worker events occurred between requested_at and reported_at?
import json
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

for req in sample_requests:
    cid = req['case_id']
    req_at = req['requested_at']
    rep_at = req['reported_at']
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_res = {s['resource_id'] for s in exp_steps}
    
    # Filter worker events
    worker_events = [
        a for a in activities 
        if req_at <= a['event_time'] <= rep_at 
        and (a['source_system'] == 'deletion_worker' or 'Deletion worker' in a['details'])
    ]
    
    print(f"\n{cid} ({req['email']}) req={req_at} rep={rep_at}")
    print(f"  Expected resources: {exp_res}")
    print(f"  Worker events in window ({len(worker_events)}):")
    for w in worker_events:
        is_exp = w['resource_id'] in exp_res
        marker = ">>> MATCHES EXPECTED" if is_exp else "   "
        print(f"    {marker} {w['activity_id']} {w['event_time']} {w['event_type']} {w['target_system']} {w['resource_id']} {w['reported_result']} | {w['details']}")
