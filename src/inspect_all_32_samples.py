import csv
import json

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    identities = {r['email']: r for r in csv.DictReader(f)}

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

print(f"{'case_id':<8} | {'status':<11} | {'rep_status':<17} | {'user_id':<8} | {'expected resources':<60}")
print("-" * 120)

for req in sample_requests:
    cid = req['case_id']
    email = req['email']
    user = identities.get(email, {})
    uid = user.get('user_id', '')
    exp = golden[cid]
    status = exp['deletion_status']
    rep_status = req['reported_status']
    steps = json.loads(exp['steps_json'])
    res_list = [f"{s['system_id']}:{s['resource_id']}" for s in steps]
    print(f"{cid:<8} | {status:<11} | {rep_status:<17} | {uid:<8} | {', '.join(res_list)}")
