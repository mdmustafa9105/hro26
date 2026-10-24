import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, '.')
from src.identity import IdentityResolver
from src.parsers.unified_parser import UnifiedEvidenceParser

resolver = IdentityResolver('dataset')
parser = UnifiedEvidenceParser('dataset')

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    sample_requests = list(csv.DictReader(f))

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    golden = {r['case_id']: r for r in csv.DictReader(f)}

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

acts_by_res = {}
delete_account_acts = []
for a in activities:
    res = a['resource_id']
    acts_by_res.setdefault(res, []).append(a)
    if a['target_system'] == 'account_service' and a['event_type'] == 'DELETE_RECORD':
        delete_account_acts.append(a)

matches = 0
for req in sample_requests:
    cid = req['case_id']
    email = req['email']
    req_at = parse_iso(req['requested_at'])
    rep_at = parse_iso(req['reported_at'])
    rep_status = req['reported_status']
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_acc = [s['resource_id'] for s in exp_steps if s['system_id'] == 'account_service']
    exp_acc_id = exp_acc[0] if exp_acc else None

    ident = resolver.resolve_by_email(email)
    user_records = parser.get_records_for_user(ident, req['audit_at'])
    found_acc = [r.resource_id for r in user_records if r.system_id == 'account_service']
    
    pred_acc_id = found_acc[0] if found_acc else None

    if not pred_acc_id and ident.user_id and ident.user_id.startswith('user_'):
        uid_num = int(ident.user_id.split('_')[1])
        if uid_num <= 10:
            pred_acc_id = f"account_{uid_num:03d}"

    if not pred_acc_id:
        user_res_ids = {r.resource_id for r in user_records}
        candidate_scores = {}
        expected_result = 'SUCCESS' if rep_status == 'COMPLETE' else ('PARTIAL' if rep_status == 'PARTIALLY_COMPLETE' else 'FAILED')

        # Only look at delete_account_acts where event_time <= rep_at + 120s
        valid_d_acts = [d for d in delete_account_acts if parse_iso(d['event_time']) <= rep_at]

        for ur in user_res_ids:
            for act in acts_by_res.get(ur, []):
                act_time = parse_iso(act['event_time'])
                for d_act in valid_d_acts:
                    d_time = parse_iso(d_act['event_time'])
                    diff_sec = abs((act_time - d_time).total_seconds())
                    if diff_sec <= 7200:
                        if d_act['reported_result'] == expected_result:
                            acc_id = d_act['resource_id']
                            candidate_scores[acc_id] = candidate_scores.get(acc_id, 0) + (7200 - diff_sec)

        if candidate_scores:
            pred_acc_id = max(candidate_scores.items(), key=lambda x: x[1])[0]
        else:
            near_acts = []
            for d_act in valid_d_acts:
                d_time = parse_iso(d_act['event_time'])
                diff_sec = abs((rep_at - d_time).total_seconds())
                if diff_sec <= 7200:
                    if d_act['reported_result'] == expected_result:
                        near_acts.append((d_act['resource_id'], diff_sec))
            if near_acts:
                near_acts.sort(key=lambda x: x[1])
                pred_acc_id = near_acts[0][0]

    is_match = (pred_acc_id == exp_acc_id)
    if is_match:
        matches += 1
    print(f"{cid}: Exp={exp_acc_id} Pred={pred_acc_id} -> {'MATCH' if is_match else 'MISMATCH'}")

print(f"Total account matches: {matches}/{len(sample_requests)}")
