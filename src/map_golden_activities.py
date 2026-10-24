import csv

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

print(f"Total system_activity events: {len(activities)}")

# Let's inspect for each case in sample_output what resources are in golden steps:
import json
for req in sample_requests:
    cid = req['case_id']
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_resources = {s['resource_id'] for s in exp_steps}
    
    # Check which activities in system_activity mention these resources
    matched_acts = [a for a in activities if a['resource_id'] in exp_resources]
    
    print(f"\n{cid} ({req['email']}) req={req['requested_at']} rep={req['reported_at']}")
    print(f"  Golden resources: {exp_resources}")
    for a in matched_acts:
        print(f"    act: {a['activity_id']} {a['event_time']} {a['event_type']} {a['resource_id']} {a['reported_result']} {a['details']}")
