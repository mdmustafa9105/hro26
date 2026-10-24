import csv

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# Let's inspect activities between 2026-08-30T10:30:00Z and 2026-08-30T14:00:00Z
window = [a for a in activities if '2026-08-30T10:30:00Z' <= a['event_time'] <= '2026-08-30T14:00:00Z']
print(f"Activities in window: {len(window)}")
for a in window:
    print(f"{a['activity_id']} | {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']} | {a['details']}")
