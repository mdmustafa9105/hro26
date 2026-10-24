import os

test_ids = ['data_flow_3518', 'backup_8264', 'support_9251', 'search_6401', 'account_4979', 'account_1506', 'account_9641']

for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                matches = [t for t in test_ids if t in c]
                if matches:
                    print(f"{f}: {matches}")
        except:
            pass
