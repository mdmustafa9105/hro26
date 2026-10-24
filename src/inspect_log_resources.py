import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

log_dir = 'dataset/evidence/logs'
for fname in sorted(os.listdir(log_dir)):
    fpath = os.path.join(log_dir, fname)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    r_matches = re.findall(r'(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)', content)
    e_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', content)
    u_matches = re.findall(r'user_\d+', content)
    if r_matches or e_matches:
        print(f"{fname}: {len(r_matches)} resources (e.g. {r_matches[:3]}), {len(e_matches)} emails, {len(u_matches)} users")
