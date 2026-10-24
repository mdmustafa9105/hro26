import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read sample requests
with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

# Read sample outputs (ONLY in this test script to verify hypothesis!)
with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    golden = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

for req in sample_requests[:10]:
    c_id = req['case_id']
    req_at = req['requested_at']
    rep_at = req['reported_at']

    # Expected resources
    exp_resources = set(s['resource_id'] for s in golden[c_id])

    # Find activities in [requested_at - 1m, reported_at + 1m]
    # where deletion_worker was acting
    window_acts = [
        a for a in activities
        if req_at <= a['event_time'] <= rep_at
        and a['source_system'] == 'deletion_worker'
    ]

    act_resources = set(a['resource_id'] for a in window_acts)

    # Intersection and differences
    print(f"\n{c_id} ({req['email']}):")
    print(f"  Window: {req_at} -> {rep_at}")
    print(f"  Expected resources ({len(exp_resources)}): {sorted(exp_resources)}")
    print(f"  Activity resources ({len(act_resources)}): {sorted(act_resources)}")
    print(f"  Match? {exp_resources.issubset(act_resources) or act_resources.issubset(exp_resources)}")
    if exp_resources - act_resources:
        print(f"  In expected but NOT in activity: {exp_resources - act_resources}")
