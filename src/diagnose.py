import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import DeletionAuditEngine

def main():
    engine = DeletionAuditEngine('dataset')
    with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
        sample_requests = list(csv.DictReader(f))
    with open('dataset/sample_output.csv', encoding='utf-8') as f:
        golden = {r['case_id']: r for r in csv.DictReader(f)}

    diff_cases = []
    for req in sample_requests:
        cid = req['case_id']
        exp = golden[cid]
        exp_status = exp['deletion_status']
        exp_steps = json.loads(exp['steps_json'])
        
        pred_status, pred_steps, unres = engine.audit_case(req)
        if pred_status != exp_status or pred_steps != exp_steps:
            diff_cases.append((cid, req, exp_status, pred_status, exp_steps, pred_steps))

    print(f"Total mismatched cases: {len(diff_cases)}")
    for cid, req, exp_status, pred_status, exp_steps, pred_steps in diff_cases:
        print(f"\n=== {cid} ({req['email']}) ===")
        print(f"Status: exp={exp_status} pred={pred_status}")
        exp_tuples = [(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state'], s['evidence_id']) for s in exp_steps]
        pred_tuples = [(s['phase'], s['system_id'], s['resource_id'], s['operation'], s['state'], s['evidence_id']) for s in pred_steps]
        
        missing = [t for t in exp_tuples if t not in pred_tuples]
        extra = [t for t in pred_tuples if t not in exp_tuples]
        
        if missing:
            print("  Missing in pred:")
            for m in missing:
                print(f"    - {m}")
        if extra:
            print("  Extra in pred:")
            for e in extra:
                print(f"    + {e}")
        if not missing and not extra:
            print("  Ordering / step_no mismatch only!")
            for idx, (es, ps) in enumerate(zip(exp_steps, pred_steps)):
                if es != ps:
                    print(f"    Step {idx+1}: Exp {es} vs Pred {ps}")

if __name__ == '__main__':
    main()
