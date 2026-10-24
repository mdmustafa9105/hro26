import csv
import json
import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.engine import DeletionAuditEngine

engine = DeletionAuditEngine('dataset')

with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

perfect_matches = []
status_only_matches = []
status_mismatches = []

categories = {
    'missing_account_absent_verification': [],
    'missing_security_audit_verification': [],
    'trace_log_parsing_issue': [],
    'status_mismatch_incomplete_vs_complete': [],
    'status_mismatch_complete_vs_incomplete': [],
    'missing_resource_association': []
}

for req in sample_requests:
    c_id = req['case_id']
    g_row = golden[c_id]
    exp_status = g_row['deletion_status']
    exp_steps = json.loads(g_row['steps_json'])

    pred_status, pred_steps, _ = engine.audit_case(req)

    if pred_status == exp_status and pred_steps == exp_steps:
        perfect_matches.append(c_id)
    elif pred_status == exp_status:
        status_only_matches.append(c_id)
        # analyze step differences
        exp_res = set(s['resource_id'] for s in exp_steps)
        pred_res = set(s['resource_id'] for s in pred_steps)
        diff_res = exp_res - pred_res
        
        has_acc = any(r.startswith('account_') for r in diff_res)
        has_sec = any(r.startswith('audit_record_') for r in diff_res)
        if has_acc and len(diff_res) == 1:
            categories['missing_account_absent_verification'].append((c_id, diff_res))
        elif has_sec and len(diff_res) == 1:
            categories['missing_security_audit_verification'].append((c_id, diff_res))
        else:
            categories['missing_resource_association'].append((c_id, diff_res))
    else:
        status_mismatches.append(c_id)
        if exp_status == 'COMPLETE' and pred_status == 'INCOMPLETE':
            categories['status_mismatch_complete_vs_incomplete'].append(c_id)
        else:
            categories['status_mismatch_incomplete_vs_complete'].append(c_id)

print(f"Perfect Matches ({len(perfect_matches)}): {perfect_matches}")
print(f"Status Only Matches ({len(status_only_matches)}): {status_only_matches}")
print(f"Status Mismatches ({len(status_mismatches)}): {status_mismatches}")

print("\n--- Failure Categories ---")
for cat, cases in categories.items():
    print(f"{cat}: {len(cases)} cases")
    for c in cases[:5]:
        print(f"  {c}")
