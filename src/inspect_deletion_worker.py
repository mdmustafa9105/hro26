import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Let's inspect the distribution of deletion_worker activities
with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    del_acts = [r for r in csv.DictReader(f) if r['source_system'] == 'deletion_worker']

print(f"Total deletion_worker activities: {len(del_acts)}")
for a in del_acts[:15]:
    print(a['activity_id'], a['event_time'], a['event_type'], a['target_system'], a['resource_id'], a['reported_result'], a['details'])
