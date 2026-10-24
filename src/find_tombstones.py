import os
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.json') or f.endswith('.txt') or f.endswith('.sql') or f.endswith('.log'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fl:
                content = fl.read()
                matches = re.findall(r'tombstone_\d+', content)
                if matches:
                    print(f"{f}: found {len(matches)} tombstones: {set(matches[:5])}")
                    # print sample context
                    idx = content.find(matches[0])
                    print("  Sample:", content[max(0, idx-50):min(len(content), idx+200)].replace('\n', ' '))
