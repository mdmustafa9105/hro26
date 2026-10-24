import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import DeletionAuditEngine

engine = DeletionAuditEngine("dataset")

with open("dataset/sample_deletion_requests.csv", mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open("dataset/sample_output.csv", mode='r', encoding='utf-8') as f:
    golden_outputs = {r['case_id']: r for r in csv.DictReader(f)}

for req in sample_requests:
    case_id = req['case_id']
    expected_row = golden_outputs.get(case_id, {})
    expected_status = expected_row.get('deletion_status')
    expected_steps = json.loads(expected_row.get('steps_json', '[]'))

    pred_status, pred_steps, unres = engine.audit_case(req)

    if pred_status != expected_status or pred_steps != expected_steps:
        print(f"\n==================== {case_id} ({req['email']}) ====================")
        print(f"Status: Expected={expected_status} vs Predicted={pred_status}")
        exp_ops = [(s['phase'], s['system_id'], s['resource_id'], s['operation'], s.get('evidence_id', '')) for s in expected_steps]
        pred_ops = [(s['phase'], s['system_id'], s['resource_id'], s['operation'], s.get('evidence_id', '')) for s in pred_steps]

        missing = [s for s in exp_ops if s not in pred_ops]
        extra = [s for s in pred_ops if s not in exp_ops]

        if missing:
            print("  MISSING steps in prediction:")
            for m in missing:
                print(f"    - {m}")
        if extra:
            print("  EXTRA steps in prediction:")
            for e in extra:
                print(f"    + {e}")
