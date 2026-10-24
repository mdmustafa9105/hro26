import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

# build email to user_id map
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
    email = req['email'].strip().lower()
    uid = email_to_uid.get(email)
    print(f"{c_id} | {email} -> {uid}")
