#!/usr/bin/env python3
import sys, io, csv, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

"""
Analyse sample cases case_05, case_11, case_21, case_32 in depth.
Hypotheses:
  (a) worker SUCCESS in system_activity is only a claim
  (b) a record is absent if a snapshot covering that system, captured
      on or before audit_at, does not contain it
  (c) records link to users by user_id, customer_reference, email,
      phone or email hash inside snapshots
"""

DATASET = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")
TARGET_CASES = ["case_05", "case_11", "case_21", "case_32"]

def load_csv(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def parse_steps(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []

def read_first_n_lines(filepath, n=40):
    full = os.path.join(DATASET, filepath)
    if not os.path.exists(full):
        return [f"  [FILE NOT FOUND: {full}]"]
    ext = os.path.splitext(full)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif"):
        return [f"  [BINARY IMAGE -- skipping]"]
    if ext == ".pdf":
        return [f"  [PDF -- skipping raw content]"]
    lines = []
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= n:
                    break
                lines.append(line.rstrip("\n\r"))
    except Exception as e:
        lines.append(f"  [READ ERROR: {e}]")
    return lines

# -- load data --
print("=" * 100)
print("LOADING DATA FILES")
print("=" * 100)

sample_requests = load_csv(os.path.join(DATASET, "sample_deletion_requests.csv"))
sample_output   = load_csv(os.path.join(DATASET, "sample_output.csv"))
user_identities = load_csv(os.path.join(DATASET, "user_identities.csv"))
user_audit_log  = load_csv(os.path.join(DATASET, "user_audit_log.csv"))
system_activity = load_csv(os.path.join(DATASET, "system_activity.csv"))
deletion_rules  = load_csv(os.path.join(DATASET, "deletion_rules.csv"))
evidence_files  = load_csv(os.path.join(DATASET, "evidence_files.csv"))

req_by_case = {r["case_id"]: r for r in sample_requests}
out_by_case = {r["case_id"]: r for r in sample_output}
evidence_by_id = {r["file_id"]: r for r in evidence_files}

id_by_email = {}
for u in user_identities:
    id_by_email.setdefault(u["email"], []).append(u)

audit_by_user = {}
for a in user_audit_log:
    audit_by_user.setdefault(a["user_id"], []).append(a)

activity_by_resource = {}
for act in system_activity:
    activity_by_resource.setdefault(act["resource_id"], []).append(act)

audit_by_old_email = {}
audit_by_new_email = {}
for a in user_audit_log:
    if a["field_name"] == "email":
        audit_by_old_email.setdefault(a["old_value"], []).append(a)
        audit_by_new_email.setdefault(a["new_value"], []).append(a)

id_by_userid = {}
for u in user_identities:
    id_by_userid[u["user_id"]] = u

print(f"  sample_requests: {len(sample_requests)}")
print(f"  sample_output:   {len(sample_output)}")
print(f"  user_identities: {len(user_identities)}")
print(f"  user_audit_log:  {len(user_audit_log)}")
print(f"  system_activity: {len(system_activity)}")
print(f"  deletion_rules:  {len(deletion_rules)}")
print(f"  evidence_files:  {len(evidence_files)}")

# system_id -> data_category mapping
SYS_TO_CAT = {
    "account_service": "USER_PROFILE",
    "search_service": "SEARCH_INDEX_ENTRY",
    "analytics_platform": "ANALYTICS_PROFILE",
    "support_platform": "SUPPORT_MESSAGE",
    "export_service": "USER_EXPORT",
    "integration_service": None,
    "backup_service": "BACKUP_ARCHIVE",
    "security_service": "SECURITY_AUDIT_LOG",
    "identity_service": "ACCOUNT_TOMBSTONE",
    "marketing_platform": "MARKETING_PROFILE",
}

for case_id in TARGET_CASES:
    print("\n" + "#" * 100)
    print(f"  CASE: {case_id}")
    print("#" * 100)

    req = req_by_case.get(case_id)
    if not req:
        print(f"  [NOT FOUND in sample_deletion_requests.csv]")
        continue

    # 1. Request row
    print(f"\n--- 1. DELETION REQUEST ---")
    for k, v in req.items():
        print(f"    {k}: {v}")

    # 2. Expected output
    out = out_by_case.get(case_id)
    if not out:
        print(f"\n  [NOT FOUND in sample_output.csv]")
        continue
    steps = parse_steps(out["steps_json"])
    print(f"\n--- 2. EXPECTED OUTPUT: status={out['deletion_status']}, {len(steps)} steps ---")
    for s in steps:
        print(f"    step {s['step_no']:2d}  {s['phase']:15s}  {s['system_id']:25s}  "
              f"{s['resource_id']:25s}  {s['operation']:30s}  {s['state']:12s}  "
              f"evidence={s['evidence_id']}")

    # 3. User identity resolution
    email = req["email"]
    print(f"\n--- 3. USER IDENTITY (email: {email}) ---")

    direct_matches = id_by_email.get(email, [])
    historical_uids = set()
    for a in audit_by_old_email.get(email, []):
        historical_uids.add(a["user_id"])
    for a in audit_by_new_email.get(email, []):
        historical_uids.add(a["user_id"])

    resolved_users = set(m["user_id"] for m in direct_matches) | historical_uids

    if not resolved_users:
        print(f"    [NO USER FOUND]")

    all_emails, all_phones, all_hashes, all_user_ids, all_names = set(), set(), set(), set(), set()

    for uid in sorted(resolved_users):
        all_user_ids.add(uid)
        u = id_by_userid.get(uid)
        if u:
            print(f"\n    CURRENT ({uid}):")
            for k, v in u.items():
                print(f"      {k}: {v}")
            all_emails.add(u["email"])
            all_phones.add(u["phone"])
            all_hashes.add(u["email_hash"])
            all_names.add(u["name"])

        audits = audit_by_user.get(uid, [])
        if audits:
            print(f"    AUDIT LOG ({len(audits)} entries):")
            for a in audits:
                print(f"      {a['audit_id']}  {a['event_time']}  "
                      f"{a['field_name']}: {a['old_value']} -> {a['new_value']}")
                if a["field_name"] == "email":
                    all_emails.add(a["old_value"])
                    all_emails.add(a["new_value"])
                elif a["field_name"] == "phone":
                    all_phones.add(a["old_value"])
                    all_phones.add(a["new_value"])
                elif a["field_name"] == "email_hash":
                    all_hashes.add(a["old_value"])
                    all_hashes.add(a["new_value"])
                elif a["field_name"] == "name":
                    all_names.add(a["old_value"])
                    all_names.add(a["new_value"])

    print(f"\n    ALL IDENTIFIERS:")
    print(f"      user_ids:     {sorted(all_user_ids)}")
    print(f"      emails:       {sorted(all_emails)}")
    print(f"      phones:       {sorted(all_phones)}")
    print(f"      email_hashes: {sorted(all_hashes)}")
    print(f"      names:        {sorted(all_names)}")

    # 4. System activity for expected resources
    resources = sorted(set(s["resource_id"] for s in steps))
    print(f"\n--- 4. SYSTEM ACTIVITY for {resources} ---")

    success_claims = []
    for rid in resources:
        acts = activity_by_resource.get(rid, [])
        if acts:
            print(f"\n    {rid} ({len(acts)} rows):")
            for act in acts:
                marker = ""
                if act.get("reported_result") == "SUCCESS":
                    marker = " <-- SUCCESS CLAIM"
                    success_claims.append(act)
                print(f"      {act['activity_id']:15s}  {act['event_time']}  "
                      f"{act['event_type']:20s}  {act['source_system']:25s} -> "
                      f"{act.get('target_system',''):25s}  result={act.get('reported_result','')}"
                      f"{marker}")
                details = act.get("details", "")
                if details:
                    print(f"        details: {details[:200]}")
        else:
            print(f"\n    {rid}: NO ACTIVITY ROWS")

    # 5. Evidence files
    cited = sorted(set(s["evidence_id"] for s in steps if s.get("evidence_id")))
    print(f"\n--- 5. EVIDENCE FILES: {cited} ---")

    for eid in cited:
        ev = evidence_by_id.get(eid)
        if not ev:
            print(f"\n    {eid}: [NOT FOUND]")
            continue
        print(f"\n    {eid}: {ev['file_path']}")
        print(f"    origin:      {ev['origin']}")
        print(f"    captured_at: {ev['captured_at']}")
        print(f"    audit_at:    {req['audit_at']}")
        cap, aud = ev["captured_at"], req["audit_at"]
        if cap <= aud:
            print(f"    [OK] captured_at <= audit_at")
        else:
            print(f"    [!!] captured_at > audit_at -- AFTER AUDIT!")
        print(f"    -- First 40 lines --")
        for line in read_first_n_lines(ev["file_path"], 40):
            print(f"    | {line}")

    # 6. Deletion rules
    print(f"\n--- 6. MATCHING DELETION RULES ---")
    seen_cats = set()
    for s in steps:
        cat = SYS_TO_CAT.get(s["system_id"])
        if cat:
            seen_cats.add(cat)
        if s["resource_id"].startswith("tombstone_"):
            seen_cats.add("ACCOUNT_TOMBSTONE")

    for rule in deletion_rules:
        if rule["data_category"] in seen_cats:
            print(f"    {rule['rule_id']:10s}  {rule['data_category']:25s}  "
                  f"{rule['condition']:60s}  -> {rule['required_action']}")

    # 7. Hypothesis checks
    print(f"\n--- 7. HYPOTHESIS CHECKS ---")

    # (a) SUCCESS is only a claim
    print(f"\n  (a) SUCCESS claims:")
    if success_claims:
        for sc in success_claims:
            rid = sc["resource_id"]
            for s in steps:
                if s["resource_id"] == rid and s["phase"] == "FINDING":
                    print(f"      {sc['activity_id']}: {sc['event_type']} on {rid} "
                          f"claimed SUCCESS at {sc['event_time']}")
                    print(f"        BUT expected output FINDING: {s['operation']} "
                          f"state={s['state']}")
                    print(f"        -> HYPOTHESIS (a) CONFIRMED: SUCCESS was a false claim")
                    break
            else:
                if out["deletion_status"] == "INCOMPLETE":
                    print(f"      {sc['activity_id']}: SUCCESS on {rid}, but case INCOMPLETE")
                elif out["deletion_status"] == "COMPLETE":
                    print(f"      {sc['activity_id']}: SUCCESS on {rid}, case COMPLETE (accurate)")
    else:
        print(f"      No SUCCESS claims for this case's resources")

    # (b) Record absence from snapshot
    print(f"\n  (b) Record absence from snapshot:")
    for s in steps:
        if s["operation"] == "VERIFY_RECORD_ABSENT" and s["evidence_id"]:
            ev = evidence_by_id.get(s["evidence_id"])
            if ev:
                print(f"      {s['resource_id']} ABSENT via {s['evidence_id']} "
                      f"(captured {ev['captured_at']})")
                if ev["captured_at"] <= req["audit_at"]:
                    print(f"        [OK] Snapshot before audit_at -- HYPOTHESIS (b) consistent")
                else:
                    print(f"        [!!] Snapshot AFTER audit_at")
        elif s["operation"] == "REPORT_REMAINING_RECORD" and s["evidence_id"]:
            ev = evidence_by_id.get(s["evidence_id"])
            if ev:
                print(f"      {s['resource_id']} PRESENT via {s['evidence_id']} "
                      f"(captured {ev['captured_at']})")

    # (c) Identifier linking
    print(f"\n  (c) Identifier linking in evidence:")
    for eid in cited:
        ev = evidence_by_id.get(eid)
        if not ev:
            continue
        full_path = os.path.join(DATASET, ev["file_path"])
        ext = os.path.splitext(full_path)[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".pdf"):
            print(f"      {eid}: binary/PDF -- cannot scan")
            continue
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            print(f"      {eid}: read error")
            continue

        found = []
        for uid in all_user_ids:
            if uid in content:
                found.append(f"user_id={uid}")
        for em in all_emails:
            if em in content:
                found.append(f"email={em}")
        for ph in all_phones:
            if ph in content:
                found.append(f"phone={ph}")
        for eh in all_hashes:
            if eh in content:
                found.append(f"hash={eh[:12]}...")
        for nm in all_names:
            if nm in content:
                found.append(f"name={nm}")
        # also look for "customer_reference"
        if "customer_reference" in content:
            for uid in all_user_ids:
                if uid.replace("user_", "") in content:
                    found.append(f"customer_ref_pattern")
                    break

        if found:
            print(f"      {eid}: MATCHED [{', '.join(found)}]")
        else:
            print(f"      {eid}: NO identifier matches")

print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
