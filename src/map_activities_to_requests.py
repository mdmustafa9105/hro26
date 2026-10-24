import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    golden = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# Look at activities where details mention account deletion or target_system is deletion target
# Let's see what activities match the resources in golden steps
all_matched = 0
for req in sample_requests:
    c_id = req['case_id']
    expected_resources = set(s['resource_id'] for s in golden[c_id])
    
    # Check which expected resources appear in system_activity
    in_act = set()
    for a in activities:
        if a['resource_id'] in expected_resources:
            in_act.add(a['resource_id'])
            
    missing_from_act = expected_resources - in_act
    print(f"{c_id}: {len(expected_resources)} expected resources | {len(in_act)} in system_activity | Missing from act: {missing_from_act}")
