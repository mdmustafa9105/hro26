import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    sample_outputs = list(csv.DictReader(f))

has_acc_verify = 0
for row in sample_outputs:
    c_id = row['case_id']
    steps = json.loads(row['steps_json'])
    acc_steps = [s for s in steps if s['system_id'] == 'account_service']
    if acc_steps:
        has_acc_verify += 1
    else:
        print(f"{c_id} has NO account_service step!")

print(f"Total cases with account_service verification: {has_acc_verify}/{len(sample_outputs)}")
