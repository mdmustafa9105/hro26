import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Build mapping from email -> user_id
email_to_user = {}

# 1. From user_identities.csv
with open('dataset/user_identities.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        u_id = row['user_id']
        email = row['email'].strip().lower()
        if email:
            email_to_user[email] = u_id

# 2. From user_audit_log.csv
with open('dataset/user_audit_log.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        u_id = row['user_id']
        field = row['field_name']
        if field == 'email':
            old_val = row['old_value'].strip().lower()
            new_val = row['new_value'].strip().lower()
            if old_val:
                email_to_user[old_val] = u_id
            if new_val:
                email_to_user[new_val] = u_id

# Check sample_deletion_requests.csv
sample_unresolved = 0
with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        email = row['email'].strip().lower()
        if email not in email_to_user:
            print(f"Sample unmapped: case_id={row['case_id']}, email={email}")
            sample_unresolved += 1

print(f"Sample deletion requests: {32 - sample_unresolved}/32 resolved")

# Check deletion_requests.csv
real_unresolved = 0
with open('dataset/deletion_requests.csv', mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        email = row['email'].strip().lower()
        if email not in email_to_user:
            print(f"Real unmapped: case_id={row['case_id']}, email={email}")
            real_unresolved += 1

print(f"Full deletion requests: {518 - real_unresolved}/518 resolved")
