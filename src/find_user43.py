import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for root, dirs, files in os.walk('dataset'):
    for f in files:
        if f.endswith('.csv') or f.endswith('.sql') or f.endswith('.json') or f.endswith('.log') or f.endswith('.txt'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fl:
                text = fl.read()
                if 'account_7566' in text or 'user_43' in text:
                    print(f"Found in {f}: {'account_7566' if 'account_7566' in text else ''} {'user_43' if 'user_43' in text else ''}")
