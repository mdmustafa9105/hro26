import os

audit_ids = ['audit_record_7068', 'audit_record_6909', 'audit_record_1707', 'audit_record_3954']

for root, dirs, files in os.walk('dataset'):
    for file in files:
        if file.endswith(('.csv', '.json', '.sql', '.txt', '.log')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for aid in audit_ids:
                        if aid in content:
                            print(f"Found {aid} in {path}")
            except Exception:
                pass
