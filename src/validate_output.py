import csv
import json
import sys

print("Validating output.csv...")
with open("output.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

assert fieldnames == ["case_id", "deletion_status", "steps_json"], f"Invalid columns: {fieldnames}"
assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"

allowed_statuses = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
allowed_phases = {"FINDING", "REMEDIATION", "VERIFICATION"}
allowed_operations = {
    "REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK",
    "DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD",
    "VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED", "VERIFY_RECORD_ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"
}
allowed_states = {"PRESENT", "ABSENT", "REDACTED", "ANONYMIZED", "ACTIVE", "DISABLED", "BLOCKED"}

status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

for idx, r in enumerate(rows, start=1):
    cid = r["case_id"]
    status = r["deletion_status"]
    steps_raw = r["steps_json"]

    assert status in allowed_statuses, f"Row {idx} ({cid}) has invalid status: {status}"
    status_counts[status] += 1

    steps = json.loads(steps_raw)
    assert isinstance(steps, list), f"Row {idx} steps_json is not a list"

    if status == "NOT_APPLICABLE":
        assert len(steps) == 0, f"Row {idx} ({cid}) NOT_APPLICABLE must have empty steps"

    if status == "INCOMPLETE":
        assert len(steps) > 0, f"CRITICAL VIOLATION: Row {idx} ({cid}) INCOMPLETE has EMPTY steps!"

    # Check phase ordering and numbering
    cur_phase_idx = 0
    phase_order_map = {"FINDING": 0, "REMEDIATION": 1, "VERIFICATION": 2}

    for s_idx, step in enumerate(steps, start=1):
        assert step["step_no"] == s_idx, f"Row {idx} ({cid}) step_no mismatch: expected {s_idx}, got {step['step_no']}"
        assert step["phase"] in allowed_phases, f"Row {idx} ({cid}) invalid phase: {step['phase']}"
        assert step["operation"] in allowed_operations, f"Row {idx} ({cid}) invalid op: {step['operation']}"
        assert step["state"] in allowed_states, f"Row {idx} ({cid}) invalid state: {step['state']}"
        assert "system_id" in step and step["system_id"], f"Row {idx} ({cid}) missing system_id"
        assert "resource_id" in step and step["resource_id"], f"Row {idx} ({cid}) missing resource_id"

        p_idx = phase_order_map[step["phase"]]
        assert p_idx >= cur_phase_idx, f"Row {idx} ({cid}) phase ordering violation: {step['phase']} after higher phase"
        cur_phase_idx = p_idx

        # Check evidence_id rules
        if status == "COMPLETE":
            assert step["evidence_id"] != "", f"Row {idx} ({cid}) COMPLETE verification must cite evidence_id"
        elif status == "INCOMPLETE":
            if step["phase"] in ("REMEDIATION", "VERIFICATION"):
                assert step["evidence_id"] == "", f"Row {idx} ({cid}) INCOMPLETE remediation/verification must have empty evidence_id"
            elif step["phase"] == "FINDING":
                assert step["evidence_id"] != "", f"Row {idx} ({cid}) finding must cite evidence_id"

print("=" * 60)
print("OUTPUT VALIDATION PASSED SUCCESSFULLY!")
print("=" * 60)
print(f"Total Rows:         {len(rows)}")
print(f"COMPLETE:           {status_counts['COMPLETE']}")
print(f"INCOMPLETE:         {status_counts['INCOMPLETE']}")
print(f"NOT_APPLICABLE:     {status_counts['NOT_APPLICABLE']}")
print("All contract requirements strictly verified.")
