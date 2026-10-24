import csv

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

deletion_ops = [
    'DELETE_RECORD', 'REDACT_RECORD', 'ANONYMIZE_RECORD', 
    'DISABLE_DATA_FLOW', 'BLOCK_RESTORE', 'CHECK_DATA_FLOW', 'CHECK_RESTORE_ACCESS'
]

worker_acts = [a for a in activities if a['event_type'] in deletion_ops or 'deletion_worker' in a['source_system']]
print(f"Total worker activities: {len(worker_acts)}")

# Let's inspect the distribution of event_time and target_system
for a in worker_acts[:30]:
    print(a['activity_id'], a['event_time'], a['event_type'], a['target_system'], a['resource_id'], a['reported_result'], a['details'])
