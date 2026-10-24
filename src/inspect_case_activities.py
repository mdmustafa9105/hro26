import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    all_activities = list(csv.DictReader(f))

for req in sample_requests[:10]:
    c_id = req['case_id']
    req_at = req['requested_at']
    rep_at = req['reported_at']
    
    # find activities in window [requested_at - 10m, reported_at + 10m]
    # where source or target is deletion_worker or event_type in (DELETE_RECORD, REDACT_RECORD, ANONYMIZED, etc.)
    acts = []
    for a in all_activities:
        t = a['event_time']
        if req_at <= t <= rep_at:
            if a['source_system'] == 'deletion_worker' or 'deletion' in a['source_system'] or 'deletion' in a['details'].lower():
                acts.append(a)
    print(f"\n{c_id} (req: {req_at} -> rep: {rep_at}): found {len(acts)} deletion activities:")
    for a in acts:
        print(f"  {a['event_time']} | {a['event_type']} | {a['source_system']} -> {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
