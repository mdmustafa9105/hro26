import csv
import json
import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.engine import DeletionAuditEngine

def evaluate():
    dataset_dir = 'dataset'
    samples_path = os.path.join(dataset_dir, 'sample_deletion_requests.csv')
    golden_path = os.path.join(dataset_dir, 'sample_output.csv')

    with open(samples_path, mode='r', encoding='utf-8') as f:
        sample_requests = list(csv.DictReader(f))

    with open(golden_path, mode='r', encoding='utf-8') as f:
        golden_outputs = {r['case_id']: r for r in csv.DictReader(f)}

    engine = DeletionAuditEngine(dataset_dir)

    # Regression check: completed lookup or scan event with rows="0" or http_status="404" means ABSENT
    ev_34_recs = engine.evidence_parser.records_by_file_id.get('evidence_34', [])
    rec_map = {r.resource_id: r for r in ev_34_recs}
    for acc_id in ['account_7653', 'account_3016', 'account_8590']:
        if acc_id not in rec_map:
            raise AssertionError(f"Regression check failed: {acc_id} missing in evidence_34")
        if rec_map[acc_id].state != 'ABSENT':
            raise AssertionError(f"Regression check failed: {acc_id} in evidence_34 must be ABSENT, found {rec_map[acc_id].state}")

    total_cases = len(sample_requests)
    status_matches = 0
    sequence_matches = 0
    total_expected_steps = 0
    total_predicted_steps = 0
    matched_steps = 0

    mismatches = []
    unresolved_cases = []

    for req in sample_requests:
        case_id = req['case_id']
        expected_row = golden_outputs.get(case_id, {})
        expected_status = expected_row.get('deletion_status')
        expected_steps = json.loads(expected_row.get('steps_json', '[]'))
        pred_status, pred_steps, unresolved_reason = engine.audit_case(req)

        if unresolved_reason:
            unresolved_cases.append({
                'case_id': case_id,
                'email': req.get('email', ''),
                'reason': unresolved_reason
            })

        # 1. Status accuracy
        status_ok = (pred_status == expected_status)
        if status_ok:
            status_matches += 1

        # 2. Sequence accuracy
        seq_ok = (pred_status == expected_status and pred_steps == expected_steps)
        if seq_ok:
            sequence_matches += 1
        # 3. Step level match
        total_expected_steps += len(expected_steps)
        total_predicted_steps += len(pred_steps)

        # Count matched steps
        exp_tuples = [(s.get('phase'), s.get('system_id'), s.get('resource_id'), s.get('operation'), s.get('state'), s.get('evidence_id')) for s in expected_steps]
        pred_tuples = [(s.get('phase'), s.get('system_id'), s.get('resource_id'), s.get('operation'), s.get('state'), s.get('evidence_id')) for s in pred_steps]

        for pt in pred_tuples:
            if pt in exp_tuples:
                matched_steps += 1

        if not seq_ok:
            mismatches.append({
                'case_id': case_id,
                'email': req.get('email'),
                'expected_status': expected_status,
                'predicted_status': pred_status,
                'expected_step_count': len(expected_steps),
                'predicted_step_count': len(pred_steps),
                'expected_steps': expected_steps,
                'predicted_steps': pred_steps
            })

    # Save unresolved cases if any
    if unresolved_cases:
        with open('unresolved.csv', mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['case_id', 'email', 'reason'])
            writer.writeheader()
            writer.writerows(unresolved_cases)

    if mismatches:
        print(f"\nMISMATCH DETAILS ({len(mismatches)} cases):")
        for m in mismatches[:10]:
            print(f"\n--- {m['case_id']} ({m['email']}) ---")
            print(f"  Status: Expected={m['expected_status']} vs Predicted={m['predicted_status']}")
            print(f"  Step Count: Expected={m['expected_step_count']} vs Predicted={m['predicted_step_count']}")
            print("  Expected Steps:")
            for s in m['expected_steps']:
                print(f"    [{s.get('phase')}] {s.get('system_id')} {s.get('resource_id')} {s.get('operation')} {s.get('state')} {s.get('evidence_id')}")
            print("  Predicted Steps:")
            for s in m['predicted_steps']:
                print(f"    [{s.get('phase')}] {s.get('system_id')} {s.get('resource_id')} {s.get('operation')} {s.get('state')} {s.get('evidence_id')}")

    status_acc = (status_matches / total_cases) * 100
    seq_acc = (sequence_matches / total_cases) * 100
    precision = (matched_steps / total_predicted_steps * 100) if total_predicted_steps > 0 else 0
    recall = (matched_steps / total_expected_steps * 100) if total_expected_steps > 0 else 0

    print("\n" + "=" * 80)
    print("EVALUATION REPORT")
    print("=" * 80)
    print(f"Total Cases:            {total_cases}")
    print(f"Status Accuracy:        {status_matches}/{total_cases} ({status_acc:.2f}%)")
    print(f"Sequence Accuracy:      {sequence_matches}/{total_cases} ({seq_acc:.2f}%)")
    print(f"Step Precision:         {matched_steps}/{total_predicted_steps} ({precision:.2f}%)")
    print(f"Step Recall:            {matched_steps}/{total_expected_steps} ({recall:.2f}%)")
    print(f"Unresolved Cases:       {len(unresolved_cases)}")
    print("=" * 80)

if __name__ == '__main__':
    evaluate()
