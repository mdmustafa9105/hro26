import os
import glob

search_ids = ['account_5521', 'account_6440', 'account_5037', 'audit_record_6645', 'analytics_5335']

for root, dirs, files in os.walk('dataset'):
    for file in files:
        if file.endswith(('.csv', '.json', '.sql', '.txt', '.log')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for sid in search_ids:
                        if sid in content:
                            print(f"Found {sid} in {path}")
            except Exception as e:
                pass
