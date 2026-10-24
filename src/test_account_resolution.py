import csv
import json
import os
import sys

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

# Let's index activities
# 1. Activities by resource_id
acts_by_res = {}
# 2. Delete account activities
delete_account_acts = []
# 3. Direct linked resources from LINK_RESOURCE_IDENTITY or details
links_by_ident = {}

for a in activities:
    res = a['resource_id']
    acts_by_res.setdefault(res, []).append(a)
    if a['target_system'] == 'account_service' and a['event_type'] == 'DELETE_RECORD':
        delete_account_acts.append(a)

for req in sample_requests:
    cid = req['case_id']
    email = req['email']
    req_at = req['requested_at']
    rep_at = req['reported_at']
    rep_status = req['reported_status']
    exp_steps = json.loads(golden[cid]['steps_json'])
    exp_acc = [s['resource_id'] for s in exp_steps if s['system_id'] == 'account_service']
    exp_acc_id = exp_acc[0] if exp_acc else None

    ident = resolver.resolve_by_email(email)
    user_records = parser.get_records_for_user(ident, req['audit_at'])
    found_acc = [r.resource_id for r in user_records if r.system_id == 'account_service']
    
    # If not in direct records, find candidates in delete_account_acts
    pred_acc_id = found_acc[0] if found_acc else None
    
    if not pred_acc_id:
        # Check if any user_record resource is in an activity batch with an account
        user_res_ids = {r.resource_id for r in user_records}
        candidate_accounts = set()
        for ur in user_res_ids:
            # find activities touching ur
            for act in acts_by_res.get(ur, []):
                act_time = act['event_time']
                # find delete_account_acts within 2 hours of act_time
                for d_act in delete_account_acts:
                    # check time proximity
                    if abs((int(act_time[:10].replace('-','')) - int(d_act['event_time'][:10].replace('-','')))) <= 1:
                        if req_at <= d_act['event_time'] <= rep_at or abs(len(d_act['event_time']) - len(rep_at)) >= 0:
                            # check reported_status correlation
                            expected_result = 'SUCCESS' if rep_status == 'COMPLETE' else ('PARTIAL' if rep_status == 'PARTIALLY_COMPLETE' else 'FAILED')
                            if d_act['reported_result'] == expected_result:
                                candidate_accounts.add(d_act['resource_id'])
        
        # If candidate found
        if len(candidate_accounts) == 1:
            pred_acc_id = list(candidate_accounts)[0]
        else:
            # Fallback: look around reported_at
            near_acts = []
            expected_result = 'SUCCESS' if rep_status == 'COMPLETE' else ('PARTIAL' if rep_status == 'PARTIALLY_COMPLETE' else 'FAILED')
            for d_act in delete_account_acts:
                if d_act['reported_result'] == expected_result:
                    # within +/- 2 hours of reported_at
                    # compare date and hour
                    if d_act['event_time'][:13] == rep_at[:13] or d_act['event_time'][:10] == rep_at[:10]:
                        near_acts.append(d_act)
            if len(near_acts) == 1:
                pred_acc_id = near_acts[0]['resource_id']
            elif len(candidate_accounts) > 1:
                pred_acc_id = list(candidate_accounts)[0]

    match = "MATCH" if pred_acc_id == exp_acc_id else "MISMATCH"
    print(f"{cid}: Exp={exp_acc_id} Pred={pred_acc_id} -> {match}")
