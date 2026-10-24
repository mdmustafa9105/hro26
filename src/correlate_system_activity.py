import csv

cases = ['case_21', 'case_18', 'case_20', 'case_12', 'case_15', 'case_16', 'case_17']

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    requests = {r['case_id']: r for r in csv.DictReader(f) if r['case_id'] in cases}

print("Sample requests:")
for cid, r in requests.items():
    print(cid, r['email'], "requested_at:", r['requested_at'], "reported_at:", r['reported_at'])

# Now let's see system_activity events around those timestamps!
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

for cid, r in requests.items():
    req_at = r['requested_at']
    rep_at = r['reported_at']
    print(f"\n--- Events between requested_at and reported_at for {cid} ({req_at} -> {rep_at}) ---")
    matched = [a for a in activities if req_at <= a['event_time'] <= rep_at]
    for m in matched:
        print(" ", m['activity_id'], m['event_time'], m['event_type'], m['target_system'], m['resource_id'], m['reported_result'], m['details'])
