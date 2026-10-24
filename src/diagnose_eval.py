import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import DeletionAuditEngine

def diagnose():
    dataset_dir = 'dataset'
    samples_path = os.path.join(dataset_dir, 'sample_deletion_requests.csv')
    golden_path = os.path.join(dataset_dir, 'sample_output.csv')

    with open(samples_path, mode='r', encoding='utf-8') as f:
        sample_requests = list(csv.DictReader(f))

    with open(golden_path, mode='r', encoding='utf-8') as f:
        golden_outputs = {r['case_id']: r for r in csv.DictReader(f)}

    engine = DeletionAuditEngine(dataset_dir)

    for req in sample_requests:
        case_id = req['case_id']
        expected_row = golden_outputs.get(case_id, {})
        expected_status = expected_row.get('deletion_status')
        expected_steps = json.loads(expected_row.get('steps_json', '[]'))

        pred_status, pred_steps, unresolved_reason = engine.audit_case(req)

        status_ok = (pred_status == expected_status)
        seq_ok = (pred_status == expected_status and pred_steps == expected_steps)

        if not seq_ok:
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
            if not missing and not extra:
                print("  Steps match set-wise, but order differs!")
                print("    Expected order:", [s['resource_id'] for s in expected_steps])
                print("    Predicted order:", [s['resource_id'] for s in pred_steps])

if __name__ == '__main__':
    diagnose()
