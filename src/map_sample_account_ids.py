import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    sample_outputs = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

# user identity
email_to_uid = {}
with open('dataset/user_identities.csv', mode='r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        email_to_uid[r['email'].strip().lower()] = r['user_id'].strip()
with open('dataset/user_audit_log.csv', mode='r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].strip().lower()] = r['user_id'].strip()
            email_to_uid[r['new_value'].strip().lower()] = r['user_id'].strip()

for req in sample_requests:
    c_id = req['case_id']
    uid = email_to_uid.get(req['email'].strip().lower())
    exp_acc = [s['resource_id'] for s in sample_outputs[c_id] if s['system_id'] == 'account_service'][0]
    
    # Check sources where exp_acc appears:
    sources = []
    # 1. default convention
    if uid and f"account_{int(uid.split('_')[1]):03d}" == exp_acc:
        sources.append("default_uid")
    # 2. in system activity
    act_matches = [a for a in acts if a['resource_id'] == exp_acc]
    if act_matches:
        sources.append(f"activity({len(act_matches)})")
    print(f"{c_id} ({uid}): exp_account={exp_acc} -> sources: {sources}")
