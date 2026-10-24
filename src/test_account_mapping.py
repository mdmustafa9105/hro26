import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    golden = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', mode='r', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

# build email to user_id map
email_to_uid = {}
with open('dataset/user_identities.csv', mode='r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        email_to_uid[r['email'].strip().lower()] = r['user_id'].strip()

for req in sample_requests:
    c_id = req['case_id']
    uid = email_to_uid.get(req['email'].strip().lower())
    # find expected account resource
    exp_acc = [s['resource_id'] for s in golden[c_id] if s['system_id'] == 'account_service']
    
    # check default account name
    default_acc = None
    if uid and uid.startswith('user_'):
        default_acc = f"account_{int(uid.split('_')[1]):03d}"
        
    print(f"{c_id} ({uid}): exp_account={exp_acc}, default_acc={default_acc}")
