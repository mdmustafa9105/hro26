import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sample_resources = ['account_001', 'account_002', 'account_004', 'account_006', 'account_007', 'account_008', 'account_010', 'account_7566', 'audit_record_2016']

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['resource_id'] in sample_resources:
            print(f"{row['resource_id']} | {row['event_time']} | {row['event_type']} | {row['source_system']} -> {row['target_system']} | {row['details']}")
