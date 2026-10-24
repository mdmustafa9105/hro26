import csv

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# Let's inspect the intervals between activities
print("Examining activity sequences...")
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker' or 'Deletion worker' in a['details']]

print(f"Total worker activities: {len(worker_acts)}")
# Let's see some patterns:
# Does details have any user reference or request reference?
for a in worker_acts[:15]:
    print(a['activity_id'], a['event_time'], a['event_type'], a['target_system'], a['resource_id'], a['reported_result'], '|', a['details'])
