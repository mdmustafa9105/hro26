import csv

cases = ['case_10', 'case_12', 'case_15', 'case_16', 'case_17', 'case_19', 'case_26']

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    requests = {r['case_id']: r for r in csv.DictReader(f) if r['case_id'] in cases}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

import json
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

for cid, r in requests.items():
    print(f"\n=== {cid} ({r['email']}) req={r['requested_at']} rep={r['reported_at']} audit={r['audit_at']} ===")
    exp_steps = json.loads(golden[cid]['steps_json'])
    print("Expected steps:")
    for s in exp_steps:
        print(f"  [{s['phase']}] {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} {s['evidence_id']}")
    
    # Check all activities within +/- 48h of reported_at or requested_at
    req_at = r['requested_at']
    rep_at = r['reported_at']
    # Let's find activities that match the expected resources
    exp_res = {s['resource_id'] for s in exp_steps}
    print("Matching activities for expected resources:")
    for a in activities:
        if a['resource_id'] in exp_res:
            print(f"  {a['activity_id']} {a['event_time']} {a['event_type']} {a['target_system']} {a['resource_id']} {a['reported_result']} | {a['details']}")
