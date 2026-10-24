import csv
import json

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# For every case, let's see which activities match its golden resources:
for req in sample_requests:
    cid = req['case_id']
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_res = {s['resource_id']: s['system_id'] for s in exp_steps}
    
    # All activities that touch any of these resources:
    acts = [a for a in activities if a['resource_id'] in exp_res]
    
    print(f"\n{cid} ({req['email']}) reported_at={req['reported_at']} status={req['reported_status']}")
    print(f"  Golden resources: {list(exp_res.keys())}")
    for a in acts:
        print(f"    {a['activity_id']} | {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
