import csv

search_ids = ['account_5521', 'account_6440', 'account_5037', 'audit_record_6645', 'analytics_5335']

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        for sid in search_ids:
            if sid in row.values() or any(sid in str(v) for v in row.values()):
                print(row)
