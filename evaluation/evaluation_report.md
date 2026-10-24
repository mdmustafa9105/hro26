# Evaluation Report: Ghost Data Still Exists Deletion-Audit Engine

## 1. Executive Summary & Benchmark Metrics

> [!IMPORTANT]
> **Sample Dataset Qualification**: The 100.00% (32/32) status accuracy reported below is measured exclusively on the participant-facing public sample dataset (`dataset/sample_deletion_requests.csv` with 32 cases) used to develop and calibrate the engine. **It is not an accuracy estimate on the 518 hidden evaluation cases.**
>
> On the hidden set, auditability and heuristics analysis reveals:
> - **Citation Audit Pass Rate**: **99.09% (1,088 / 1,098 citations passed)** in `output.csv` (100.00% / 75 of 75 passed on sample outputs). All 10 failed citations correspond to cases 433–442 referencing point-in-time readback log `evidence_67`.
> - **Heuristics & Review Queue Size**: **441 of 518 hidden cases (85.14%)** relied on timing offset tiebreakers, analytics time-correlation fallbacks, pipeline lag heuristics, user_id number derivations, or OCR text proximity bindings (cataloged in `review_queue.csv`).

| Metric | Score | Details |
| :--- | :--- | :--- |
| **Sample Deletion-Status Accuracy** | **100.00% (32/32)** | Accuracy on public sample dataset (`sample_output.csv`); not a hidden-set estimate |
| **Sample Sequence Accuracy (Exact Match)** | **93.75% (30/32)** | Exact match across all phases, systems, resources, operations, states, and citations |
| **Sample Step-Level Precision** | **100.00% (191/191)** | 191 of 191 emitted audit steps match canonical steps with zero false positives |
| **Sample Step-Level Recall** | **98.96% (191/193)** | 191 of 193 canonical audit steps recovered from multi-system evidence |
| **Evidence Citation Pass Rate (Sample)** | **100.00% (75/75)** | Verified against raw evidence files, OCR transcripts, and documented bindings |
| **Evidence Citation Pass Rate (Full 518)** | **99.09% (1088/1098)** | 1,088 of 1,098 non-empty citations grounded; 10 cases cite point-in-time log `evidence_67` |
| **Review Queue Size (Heuristic Cases)** | **441 / 518 (85.14%)** | Cases utilizing timing tiebreakers, pipeline lag, or fallbacks (logged in `review_queue.csv`) |
| **Unresolved Cases** | **0 (0.00%)** | 0 cases routed to `unresolved.csv` |

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

During development and iterative evaluation, critical edge cases and failure modes were systematically diagnosed and resolved:

### 3.1 Trace ID Correlation in Log Parser
- **Issue**: Structured and unstructured service logs frequently split identity references (e.g., `subject_key`, `correlation_key`, `user_id`) and resource operational events across multiple lines tied together only by `trace_id`.
- **Improvement**: Implemented a two-pass parser in `src/parsers/log_parser.py` that collects all identity mappings associated with each `trace_id` in Pass 1 and attaches them to all resource records sharing that `trace_id` in Pass 2.

### 3.2 Generalized Account Resolution
- **Issue**: Early iterations struggled to disambiguate concurrent accounts deleted near the reported timestamp, risking false cross-user associations.
- **Improvement**: Engineered a strict four-tiered account resolution strategy:
  1. Direct evidence binding if evidence explicitly names the user's identifiers (captured on or after `requested_at`).
  2. Disqualification of competitor accounts explicitly tied to other users in parsed evidence.
  3. Soft filtering on reported status vs worker result (`SUCCESS`, `PARTIAL`, `FAILED`).
  4. Deterministic pipeline-lag range tiebreakers based on platform stage latencies (`STAGE_LAGS`), with worker cadence ranking as final fallback.

### 3.3 Evidence-Based Analytics Profile Linking
- **Issue**: Fix A relied on time-delta proximity heuristics to associate anonymized analytics profiles, which could be ambiguous in high-throughput environments.
- **Improvement**: Replaced primary time-delta matching with evidence-based linking (log traces, snapshot bundles, explicit activity link events), preserving time correlation solely as a logged fallback.

### 3.4 Spatial Proximity in Multimodal OCR and PDF Parsing
- **Issue**: Screenshots and document attachments containing multiple records in tabular formats assigned arbitrary user emails to all resources on the page.
- **Improvement**: Enhanced `src/parsers/image_parser.py` and `src/parsers/pdf_parser.py` to calculate spatial text proximity, binding each resource specifically to its row-level user or email.

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
