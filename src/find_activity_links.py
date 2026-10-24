import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check all activities mentioning account_
with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    account_acts = [r for r in csv.DictReader(f) if r['resource_id'].startswith('account_')]

print(f"Total account_* activities: {len(account_acts)}")
for a in account_acts[:10]:
    print(a['activity_id'], a['event_time'], a['event_type'], a['resource_id'], a['reported_result'], a['details'])
