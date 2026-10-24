import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get case_01 details
with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    case01 = next(r for r in csv.DictReader(f) if r['case_id'] == 'case_01')

print("case_01:", case01)

# Check all activities between requested_at and reported_at or around that time
with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        # Check if event_time is within 1 day of requested_at
        if '2026-08-20' in r['event_time']:
            print(f"{r['activity_id']} | {r['event_time']} | {r['event_type']} | {r['source_system']} -> {r['target_system']} | {r['resource_id']} | {r['details']}")
