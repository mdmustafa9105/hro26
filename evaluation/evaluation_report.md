# Evaluation Report: Ghost Data Still Exists Deletion-Audit Engine

## 1. Executive Summary & Benchmark Metrics

> [!IMPORTANT]
> **Sample Dataset Qualification**: The 100.00% (32/32) status accuracy reported below is measured exclusively on the participant-facing public sample dataset (`dataset/sample_deletion_requests.csv` with 32 cases) used to develop and calibrate the engine. **It is not an accuracy estimate on the 518 hidden evaluation cases.**
>
> On the hidden set, auditability and heuristics analysis reveals:
> - **Citation Audit Pass Rate**: **100.00% (1,112 / 1,112 citations passed)** in `output.csv` (100.00% / 75 of 75 passed on sample outputs). All citations strictly verified against participant-facing evidence files.
> - **Heuristics & Review Queue Size**: **431 of 518 hidden cases (83.20%)** relied on timing offset tiebreakers, analytics time-correlation fallbacks, pipeline lag heuristics, user_id number derivations, or OCR text proximity bindings (cataloged in `review_queue.csv`).

| Metric | Score | Details |
| :--- | :--- | :--- |
| **Sample Deletion-Status Accuracy** | **100.00% (32/32)** | Accuracy on public sample dataset (`sample_output.csv`); not a hidden-set estimate |
| **Sample Sequence Accuracy (Exact Match)** | **90.62% (29/32)** | Exact match across all phases, systems, resources, operations, states, and citations |
| **Sample Step-Level Precision** | **99.48% (190/191)** | 190 of 191 emitted audit steps match canonical steps with zero false positives |
| **Sample Step-Level Recall** | **98.45% (190/193)** | 190 of 193 canonical audit steps recovered from multi-system evidence |
| **Evidence Citation Pass Rate (Sample)** | **100.00% (75/75)** | Verified against raw evidence files, OCR transcripts, and documented bindings |
| **Evidence Citation Pass Rate (Full 518)** | **100.00% (1112/1112)**| 1,112 of 1,112 non-empty citations grounded; 0 ungrounded citations |
| **Grounding Audit Pass Rate (Full 518)** | **100.00% (2991/2991)**| All 2,991 step resources grounded in dataset files or trace links (0 failures) |
| **Unresolved Cases** | **1 (0.19%)** | 1 case routed to `unresolved.csv` |

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

### 3.5 Known Limitations & Unreachable Sample Resource IDs
- **Limitation**: Exhaustive full-text, database, and OCR search across all 94 evidence files and `system_activity.csv` (via `src/audit_grounding.py`) confirms exactly three resource IDs in `dataset/sample_output.csv` that exist nowhere in the participant-facing dataset:
  1. `account_004` (in `case_04` step 1)
  2. `audit_record_6645` (in `case_18` step 11)
  3. `audit_record_5569` (in `case_20` step 7)
- **Impact**: Because these resource IDs are unfindable from raw evidence, an evidence-grounded engine cannot legitimately discover them without hardcoding or guessing. For `case_04`, the engine grounds the actual available snapshot account `account_5661`, and for cases 18 and 20, the engine omits the ungrounded audit records.

---

## 4. Participant-Created Additional Evaluation Cases (Executed Fixtures)

> [!NOTE]
> **Fixture Provenance Note**: Custom fixtures were authored after seeing engine output, and one fixture (`tombstone_register_custom_02.json`) was edited to match the production schema (`snapshots` bundle format).

Three real test case fixtures were constructed under `code/evaluation/extra_cases/` (with input deletion requests, user identities, system activities, manifests, and raw evidence logs/records) and executed through the engine using `python code/evaluation/run_extra_cases.py`.

### Fixture Directory Layout
```text
code/evaluation/extra_cases/
├── deletion_requests.csv
├── user_identities.csv
├── user_audit_log.csv
├── system_activity.csv
├── evidence_files.csv
└── evidence/
    ├── logs/
    │   └── stream_monitor_custom_01.log
    └── records/
        └── tombstone_register_custom_02.json
```

---

### Custom Case 1: Active Sync Connector with Deleted Primary Profile (`custom_01`)
- **Scenario**: The user's account was deleted in `account_service` (`account_8120`), but an active integration data connector (`data_flow_9011`) continues streaming records.
- **Input**:
  - `email`: `marcus.vance@techcorp.io`
  - `requested_at`: `2026-07-10T08:00:00Z`
  - `reported_status`: `COMPLETE` (workflow claims complete)
  - `audit_at`: `2026-07-15T12:00:00Z`
  - `request_text`: `I request full deletion of my account and all associated data streams under GDPR Article 17.`
- **Real Engine Output (`python code/evaluation/run_extra_cases.py`)**:
  - **Decision**: `INCOMPLETE`
  - **Steps Emitted (4)**:
    1. `[FINDING] integration_service data_flow_9011 REPORT_ACTIVE_DATA_FLOW ACTIVE` (cited `evidence_custom_01`)
    2. `[REMEDIATION] integration_service data_flow_9011 DISABLE_DATA_FLOW DISABLED`
    3. `[VERIFICATION] account_service account_8120 VERIFY_RECORD_ABSENT ABSENT`
    4. `[VERIFICATION] integration_service data_flow_9011 VERIFY_DATA_FLOW_DISABLED DISABLED`
- **Result & Verification**: PASS. Correctly identified that `reported_status: COMPLETE` was false due to the active sync connector, emitted finding citing `evidence_custom_01`, planned connector remediation, and verified both account absence and connector shutdown.

---

### Custom Case 2: Incomplete Tombstone Redaction (Direct PII Exposed) (`custom_02`)
- **Scenario**: An account was soft-deleted, but the tombstone record `tombstone_4491` in `identity_service` still contains unredacted email and phone numbers.
- **Input**:
  - `email`: `priya.sharma92@outlook.com`
  - `requested_at`: `2026-08-01T10:00:00Z`
  - `reported_status`: `COMPLETE`
  - `audit_at`: `2026-08-05T10:00:00Z`
  - `request_text`: `Please delete my account and ensure no personal information remains linked to my profile.`
- **Real Engine Output (`python code/evaluation/run_extra_cases.py`)**:
  - **Decision**: `INCOMPLETE`
  - **Steps Emitted (4)**:
    1. `[FINDING] identity_service tombstone_4491 REPORT_EXPOSED_PII PRESENT` (cited `evidence_custom_02`)
    2. `[REMEDIATION] identity_service tombstone_4491 REDACT_RECORD REDACTED`
    3. `[VERIFICATION] account_service account_8121 VERIFY_RECORD_ABSENT ABSENT`
    4. `[VERIFICATION] identity_service tombstone_4491 VERIFY_RECORD_REDACTED REDACTED`
- **Failures Diagnosed & Resolved**:
  - *Initial Failure*: The test fixture originally serialized JSON as a flat list, which `json_parser.py` skipped because it expected standard snapshot bundles (`{"snapshots": [...]}`).
  - *Resolution*: Updated fixture to match the production snapshot schema; the engine then successfully recognized the exposed PII on the tombstone, emitted `REPORT_EXPOSED_PII`, planned `REDACT_RECORD`, and verified both `account_8121` absence and `tombstone_4491` redaction.

---

### Custom Case 3: Subject Access Request (Non-Deletion Action) (`custom_03`)
- **Scenario**: A user submits a query in Spanish requesting copies of invoices without authorizing deletion.
- **Input**:
  - `email`: `carlos.mendez@empresa.es`
  - `requested_at`: `2026-09-12T14:30:00Z`
  - `reported_status`: `NOT_STARTED`
  - `audit_at`: `2026-09-15T14:30:00Z`
  - `request_text`: `Por favor envíenme una copia de todas mis facturas del año pasado. No quiero cerrar mi cuenta, solo necesito el archivo de exportación.`
- **Real Engine Output (`python code/evaluation/run_extra_cases.py`)**:
  - **Decision**: `NOT_APPLICABLE`
  - **Steps Emitted (0)**: `[]`
- **Result & Verification**: PASS. Non-deletion intent correctly classified via multilingual pattern analysis; emitted `NOT_APPLICABLE` with an empty steps array.
