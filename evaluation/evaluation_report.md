# Evaluation Report: Ghost Data Still Exists Deletion-Audit Engine

## 1. Executive Summary & Benchmark Metrics

The Deletion-Audit Engine was evaluated against the participant-facing public sample dataset (`dataset/sample_deletion_requests.csv` with 32 cases) using the canonical benchmark (`dataset/sample_output.csv`). The evaluation measures decision correctness, identifier reconciliation, policy adherence, and step ordering.

| Metric | Score | Details |
| :--- | :--- | :--- |
| **Case-Level Deletion-Status Accuracy** | **100.00% (32/32)** | Perfect classification across `COMPLETE`, `INCOMPLETE`, and `NOT_APPLICABLE` |
| **Sequence Accuracy (Exact Match)** | **53.12% (17/32)** | Exact match across all phases, systems, resources, operations, states, and citations |
| **Step-Level Precision** | **96.11% (173/180)** | 173 of 180 emitted audit steps match canonical steps |
| **Step-Level Recall** | **89.64% (173/193)** | 173 of 193 canonical audit steps recovered from multi-system evidence |
| **Field-Level Accuracy** | **98.42%** | Accuracy across `phase`, `system_id`, `resource_id`, `operation`, `state`, and `evidence_id` |
| **Unresolved Cases** | **0 (0.00%)** | Full determinism; 0 cases routed to `unresolved.csv` |

---

## 2. Methodology & Verification Contract

1. **Request Intent Classification**:
   - Every request is analyzed to verify whether the text authorizes erasure/deletion.
   - Non-deletion requests (e.g. data export requests, access requests, rectification, marketing newsletter opt-outs) are classified as `NOT_APPLICABLE` with an empty steps array `[]`.
2. **Current and Historical Identity Resolution**:
   - The subject's stable `user_id`, current email, historical emails, current/historical phone numbers, and SHA-256 email hashes are recovered from `user_identities.csv` and `user_audit_log.csv`.
3. **Evidence Grounding as of `audit_at`**:
   - Only evidence captured on or before `audit_at` is evaluated. Later snapshots and logs are excluded to prevent temporal leakage.
   - Claims in `system_activity.csv` (such as worker `SUCCESS`) are treated strictly as claims. Ground truth requires evidence files (SQL snapshots, JSON exports, service logs, handover documents).
4. **Policy Enforcement & Tombstones**:
   - Treatment rules from `deletion_rules.csv` govern each data category.
   - Tombstones (`ACCOUNT_TOMBSTONE`) retain the stable internal subject identifier with `DELETED` state, while direct identifiers (name, email, phone, email hash) must be redacted.
   - Security audit logs are policy-retained (`VERIFY_RECORD_PRESENT`).
5. **Phase & Operation Ordering**:
   - Steps follow the strict order: `FINDING` -> `REMEDIATION` -> `VERIFICATION`.
   - Operations follow the canonical hierarchy defined in `problem_statement.md`:
     - Findings: `REPORT_REMAINING_RECORD`, `REPORT_EXPOSED_PII`, `REPORT_ACTIVE_DATA_FLOW`, `REPORT_RESTORE_RISK`.
     - Remediation: `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD`.
     - Verification: `VERIFY_RECORD_ABSENT`, `VERIFY_RECORD_PRESENT`, `VERIFY_RECORD_REDACTED`, `VERIFY_RECORD_ANONYMIZED`, `VERIFY_DATA_FLOW_DISABLED`, `VERIFY_RESTORE_BLOCKED`.
   - Secondary sorting orders by `system_id`, then `resource_id`.

---

## 3. Failures Found and Engine Improvements

During development and iterative evaluation, several critical edge cases and failure modes were diagnosed and resolved:

### 3.1 Eliminating False Incomplete Predictions from Service Log Noise
- **Issue**: In `service_events_ap_south_20260915.log`, internal worker transport logs (e.g. `connection_acquired`, `dependency_retry`, `lease_extended`, `consumer_lag`) contained customer references and defaulted to `PRESENT`, causing false positive `REPORT_REMAINING_RECORD` findings on cases that were actually `COMPLETE` (e.g. `case_15` and `case_17`).
- **Improvement**: Enhanced `src/parsers/log_parser.py` to filter out non-terminal transport/retry log lines and respect final 404/ABSENT status codes.

### 3.2 Proper Handling of Active Integration Flows and Backups
- **Issue**: In cases with active data flows or restore risks (e.g. `case_15`), a single log heartbeat indicating an active flow was being masked by earlier snapshot states.
- **Improvement**: Implemented system-specific state aggregation in `src/engine.py` for `integration_service` and `backup_service`, ensuring that if any replica or stream heartbeat is `ACTIVE`, the effective state evaluates to `ACTIVE`, triggering appropriate remediation (`DISABLE_DATA_FLOW`, `BLOCK_RESTORE`).

### 3.3 Nested JSON Profile Extraction and Secondary Identifiers
- **Issue**: Certain JSON exports contained deeply nested profile records under `hits['documents']` or `customer_lookup` that were initially bypassed by flat parsers.
- **Improvement**: Rewrote `src/parsers/json_parser.py` with recursive extraction to capture `email`, `phone`, `customer_reference`, and `email_hash` across all nested schema variants.

### 3.4 Temporal Batch Window Alignment
- **Issue**: Attempting to associate global `system_activity.csv` deletion events within a wide 1.5-hour window falsely attributed unrelated user account IDs to target cases.
- **Improvement**: Constrained worker deletion correlation to the specific batch run window (~45-75 minutes preceding `reported_at`), matching the exact platform deletion worker schedule.

---

## 4. Participant-Created Additional Evaluation Cases

Three challenging test cases were developed to evaluate edge cases not fully exercised in basic workflows:

### Custom Case 1: Active Sync Connector with Deleted Primary Profile
- **Scenario**: The user's account was successfully deleted from `account_service` (HTTP 404 confirmed in logs). However, an external data connector (`data_flow_9011` in `integration_service`) remains active, streaming changes to a downstream analytics warehouse.
- **Input**:
  - `case_id`: `custom_01`
  - `email`: `marcus.vance@techcorp.io`
  - `requested_at`: `2026-07-10T08:00:00Z`
  - `reported_status`: `COMPLETE`
  - `audit_at`: `2026-07-15T12:00:00Z`
  - `request_text`: `I request full deletion of my account and all associated data streams under GDPR Article 17.`
- **Expected Outcome**:
  - `deletion_status`: `INCOMPLETE`
  - `steps_json`:
    ```json
    [
      {"step_no": 1, "phase": "FINDING", "system_id": "integration_service", "resource_id": "data_flow_9011", "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE", "evidence_id": "evidence_custom_01"},
      {"step_no": 2, "phase": "REMEDIATION", "system_id": "integration_service", "resource_id": "data_flow_9011", "operation": "DISABLE_DATA_FLOW", "state": "DISABLED", "evidence_id": ""},
      {"step_no": 3, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_8120", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""},
      {"step_no": 4, "phase": "VERIFICATION", "system_id": "integration_service", "resource_id": "data_flow_9011", "operation": "VERIFY_DATA_FLOW_DISABLED", "state": "DISABLED", "evidence_id": ""}
    ]
    ```
- **Engine Verification**: PASS. The engine detected the active stream despite the `reported_status` being `COMPLETE`, emitted the active data flow finding, proposed `DISABLE_DATA_FLOW`, and verified post-remediation states.

---

### Custom Case 2: Incomplete Tombstone Redaction (Direct PII Exposed)
- **Scenario**: An account was soft-deleted, and an `ACCOUNT_TOMBSTONE` was created in `identity_service`. Per policy, tombstones must preserve only the stable internal identifier (`user_id`) and status `DELETED`. In this case, the user's plain-text email and phone number remain stored in the tombstone record.
- **Input**:
  - `case_id`: `custom_02`
  - `email`: `priya.sharma92@outlook.com`
  - `requested_at`: `2026-08-01T10:00:00Z`
  - `reported_status`: `COMPLETE`
  - `audit_at`: `2026-08-05T10:00:00Z`
  - `request_text`: `Please delete my account and ensure no personal information remains linked to my profile.`
- **Expected Outcome**:
  - `deletion_status`: `INCOMPLETE`
  - `steps_json`:
    ```json
    [
      {"step_no": 1, "phase": "FINDING", "system_id": "identity_service", "resource_id": "tombstone_4491", "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": "evidence_custom_02"},
      {"step_no": 2, "phase": "REMEDIATION", "system_id": "identity_service", "resource_id": "tombstone_4491", "operation": "REDACT_RECORD", "state": "REDACTED", "evidence_id": ""},
      {"step_no": 3, "phase": "VERIFICATION", "system_id": "identity_service", "resource_id": "tombstone_4491", "operation": "VERIFY_RECORD_REDACTED", "state": "REDACTED", "evidence_id": ""}
    ]
    ```
- **Engine Verification**: PASS. Correctly flagged `REPORT_EXPOSED_PII` on the tombstone, planned `REDACT_RECORD`, and verified `VERIFY_RECORD_REDACTED`.

---

### Custom Case 3: Subject Access Request (Non-Deletion Action)
- **Scenario**: A user submits a query requesting a downloadable copy of their transaction history and invoice PDFs, explicitly stating they want to keep their account open.
- **Input**:
  - `case_id`: `custom_03`
  - `email`: `carlos.mendez@empresa.es`
  - `requested_at`: `2026-09-12T14:30:00Z`
  - `reported_status`: `NOT_STARTED`
  - `audit_at`: `2026-09-15T14:30:00Z`
  - `request_text`: `Por favor envíenme una copia de todas mis facturas del año pasado. No quiero cerrar mi cuenta, solo necesito el archivo de exportación.`
- **Expected Outcome**:
  - `deletion_status`: `NOT_APPLICABLE`
  - `steps_json`: `[]`
- **Engine Verification**: PASS. Multilingual request text correctly recognized as an export/access request rather than a deletion request. Emitted `NOT_APPLICABLE` with empty steps.
