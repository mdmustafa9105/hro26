import csv
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    sample_outputs = list(csv.DictReader(f))

for row in sample_outputs:
    c_id = row['case_id']
    status = row['deletion_status']
    steps = json.loads(row['steps_json'])
    
    findings = [s for s in steps if s['phase'] == 'FINDING']
    rem = [s for s in steps if s['phase'] == 'REMEDIATION']
    ver = [s for s in steps if s['phase'] == 'VERIFICATION']
    
    print(f"{c_id} ({status}): {len(findings)} findings, {len(rem)} rem, {len(ver)} ver")
    for f in findings:
        print(f"  FIND: {f['system_id']} {f['resource_id']} {f['operation']} {f['evidence_id']}")
    for v in ver:
        print(f"  VER : {v['system_id']} {v['resource_id']} {v['operation']} {v['state']} evidence='{v['evidence_id']}'")
