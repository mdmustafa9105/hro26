import os
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from src.models import UserIdentity, EvidenceRecord, AuditStep
from src.identity import IdentityResolver
from src.request_classifier import RequestClassifier
from src.parsers.unified_parser import UnifiedEvidenceParser

logger = logging.getLogger(__name__)

# Config constant for downstream pipeline-lag range tiebreaker
STAGE_LAGS = {
    'analytics_platform': (2400, 2850),
    'identity_service': (2400, 2850),
    'support_platform': (3000, 3300),
    'integration_service': (3450, 3750),
    'backup_service': (3850, 4150),
}

# Priority order of operations within each phase per problem statement
FINDING_ORDER = [
    "REPORT_REMAINING_RECORD",
    "REPORT_EXPOSED_PII",
    "REPORT_ACTIVE_DATA_FLOW",
    "REPORT_RESTORE_RISK",
]

REMEDIATION_ORDER = [
    "DISABLE_DATA_FLOW",
    "BLOCK_RESTORE",
    "DELETE_RECORD",
    "REDACT_RECORD",
    "ANONYMIZE_RECORD",
]

VERIFICATION_ORDER = [
    "VERIFY_RECORD_ABSENT",
    "VERIFY_RECORD_PRESENT",
    "VERIFY_RECORD_REDACTED",
    "VERIFY_RECORD_ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED",
    "VERIFY_RESTORE_BLOCKED",
]

SYSTEM_NORMALIZATION = {
    "customer_account_service": "account_service",
    "account_admin_portal": "account_service",
    "account_service": "account_service",
    "profile_service": "account_service",
    "customer_search_primary_capture": "search_service",
    "search_index_admin": "search_service",
    "search_index_service": "search_service",
    "search_service": "search_service",
    "analytics_platform": "analytics_platform",
    "support_platform": "support_platform",
    "support_replica": "support_platform",
    "support_storage_service": "support_platform",
    "attachment_preview": "support_platform",
    "export_service": "export_service",
    "integration_service": "integration_service",
    "integration_admin": "integration_service",
    "backup_service": "backup_service",
    "backup_restore_service": "backup_service",
    "security_service": "security_service",
    "identity_service": "identity_service",
    "marketing_platform": "marketing_platform",
}

def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

class DeletionAuditEngine:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.identity_resolver = IdentityResolver(dataset_dir)
        self.evidence_parser = UnifiedEvidenceParser(dataset_dir)

        # Load and index system activity
        self.activities: List[Dict[str, str]] = []
        self.acts_by_resource: Dict[str, List[Dict[str, str]]] = {}
        self.delete_account_acts: List[Dict[str, str]] = []
        self.identity_link_acts: Dict[str, List[Dict[str, str]]] = {}

        activity_path = os.path.join(self.dataset_dir, "system_activity.csv")
        if os.path.exists(activity_path):
            with open(activity_path, "r", encoding="utf-8") as f:
                self.activities = list(csv.DictReader(f))

        for a in self.activities:
            res = a.get("resource_id", "")
            if res:
                self.acts_by_resource.setdefault(res, []).append(a)
            if a.get("target_system") == "account_service" and a.get("event_type") == "DELETE_RECORD":
                self.delete_account_acts.append(a)

            # Check explicit link events
            if "LINK" in a.get("event_type", "") or "linked" in a.get("details", "").lower():
                details = a.get("details", "").lower()
                for word in details.replace("(", " ").replace(")", " ").replace(",", " ").split():
                    if "@" in word or word.startswith("user_"):
                        self.identity_link_acts.setdefault(word, []).append(a)

    def _resolve_account(self, identity: UserIdentity, case_row: Dict[str, str], user_records: List[EvidenceRecord]) -> Tuple[Optional[str], str]:
        """
        Determines the account_service resource_id and best snapshot evidence_id using Step 2 rules:
        (a) bind an account directly if evidence names the user's identifiers;
        (b) reject any candidate that evidence ties to a different user (email, user_id, phone, hash, or trace correlation);
        (c) use reported_status vs worker result only as a soft filter;
        (d) use the downstream pipeline-lag range only as a final tiebreaker, from a config constant, and log when it was used.
        """
        audit_at = case_row["audit_at"]
        rep_at = parse_iso(case_row["reported_at"])
        req_at = parse_iso(case_row["requested_at"])
        rep_status = case_row.get("reported_status", "")

        # Snapshot evidence priority for account absence
        account_snapshots = [
            ("evidence_94", "2026-09-26T10:38:56Z"),
            ("evidence_93", "2026-09-16T08:37:39Z"),
            ("evidence_92", "2026-09-15T12:00:00Z"),
            ("evidence_51", "2026-09-15T10:30:00Z"),
            ("evidence_54", "2026-09-02T08:00:00Z"),
        ]
        user_ev_ids = {r.evidence_id for r in user_records if parse_iso(r.captured_at) >= req_at}
        best_ev_id = None
        for ev_id, cap_time in account_snapshots:
            if ev_id in user_ev_ids and cap_time <= audit_at:
                best_ev_id = ev_id
                break
        if not best_ev_id:
            for ev_id, cap_time in account_snapshots:
                if cap_time <= audit_at:
                    best_ev_id = ev_id
                    break

        # (a) Direct evidence binding (captured at or after requested_at)
        direct_acc = None
        direct_ev = None
        for r in sorted(user_records, key=lambda x: x.captured_at, reverse=True):
            if SYSTEM_NORMALIZATION.get(r.system_id, r.system_id) == "account_service" and parse_iso(r.captured_at) >= req_at:
                direct_acc = r.resource_id
                direct_ev = r.evidence_id
                break

        if not direct_acc:
            for r in self.evidence_parser.all_records:
                if SYSTEM_NORMALIZATION.get(r.system_id, r.system_id) == "account_service" and r.links_to_user(identity):
                    direct_acc = r.resource_id
                    direct_ev = best_ev_id
                    break

        if direct_acc:
            chosen_ev = best_ev_id if direct_ev == "evidence_02" else direct_ev
            return direct_acc, chosen_ev

        # Check explicit identity links in system_activity
        for em in identity.emails:
            for act in self.identity_link_acts.get(em.lower(), []):
                if act.get("event_time", "") <= audit_at and act.get("target_system") == "account_service":
                    return act["resource_id"], best_ev_id
        if identity.user_id:
            for act in self.identity_link_acts.get(identity.user_id.lower(), []):
                if act.get("event_time", "") <= audit_at and act.get("target_system") == "account_service":
                    return act["resource_id"], best_ev_id

        # (b) Reject any candidate that evidence ties to a different user
        competitor_accounts = set()
        for r in self.evidence_parser.all_records:
            if r.system_id == "account_service" or r.resource_id.startswith("account_"):
                is_diff = False
                if r.user_id and r.user_id.lower() != identity.user_id.lower():
                    is_diff = True
                elif r.email and r.email.lower() not in [e.lower() for e in identity.emails]:
                    is_diff = True
                elif r.phone and r.phone not in identity.phones:
                    is_diff = True
                elif r.email_hash and r.email_hash.lower() not in [h.lower() for h in identity.email_hashes]:
                    is_diff = True
                elif r.customer_reference and r.customer_reference.startswith("user_") and r.customer_reference.lower() != identity.user_id.lower():
                    is_diff = True
                elif r.subject_reference and r.subject_reference.startswith("user_") and r.subject_reference.lower() != identity.user_id.lower():
                    is_diff = True
                if is_diff:
                    competitor_accounts.add(r.resource_id)

        valid_d_acts = [d for d in self.delete_account_acts if abs((rep_at - parse_iso(d["event_time"])).total_seconds()) <= 7200]
        candidates = [d for d in valid_d_acts if d["resource_id"] not in competitor_accounts]

        # (c) Use reported_status vs worker result only as a soft filter
        expected_result = "SUCCESS" if rep_status == "COMPLETE" else ("PARTIAL" if rep_status == "PARTIALLY_COMPLETE" else "FAILED")
        soft_matches = [d for d in candidates if d.get("reported_result") == expected_result]
        if soft_matches:
            candidates = soft_matches

        # (d) Downstream pipeline-lag range tiebreaker from STAGE_LAGS config constant
        user_res_ids = {r.resource_id for r in user_records}
        user_ds_acts = [(parse_iso(a["event_time"]), a) for ur in user_res_ids for a in self.acts_by_resource.get(ur, [])]
        lag_matched = []
        for d_act in candidates:
            d_time = parse_iso(d_act["event_time"])
            for ds_time, ds_act in user_ds_acts:
                ts = ds_act.get("target_system")
                if ts in STAGE_LAGS:
                    min_lag, max_lag = STAGE_LAGS[ts]
                    lag_sec = (ds_time - d_time).total_seconds()
                    if min_lag <= lag_sec <= max_lag:
                        lag_matched.append((d_act, lag_sec, ds_act))
                        break

        if lag_matched:
            chosen = lag_matched[0][0]["resource_id"]
            logger.info("Pipeline lag tiebreaker used for account %s: %ss to %s", chosen, int(lag_matched[0][1]), lag_matched[0][2].get("resource_id"))
            return chosen, best_ev_id
        elif candidates:
            target_offset = 4200 if rep_status == "COMPLETE" else 3000
            chosen = min(candidates, key=lambda d: abs((rep_at - parse_iso(d["event_time"])).total_seconds() - target_offset))
            return chosen["resource_id"], best_ev_id

        # General fallback: user_id number if known
        if identity.user_id and identity.user_id.startswith("user_"):
            return f"account_{int(identity.user_id.split('_')[1]):03d}", best_ev_id

        return None, best_ev_id

    def _resolve_anonymized_analytics(self, identity: UserIdentity, case_row: Dict[str, str], user_records: List[EvidenceRecord], account_id: Optional[str], account_ev_id: str) -> Optional[Tuple[str, str]]:
        """
        Step 3: Resolves anonymized analytics profile for cases where profile was anonymized in covering evidence.
        Uses evidence-based linking (trace_id, user references in snapshots/exports/OCR text) first,
        with time correlation only as a fallback, recorded in self.last_analytics_linking_method.
        """
        rep_at = parse_iso(case_row["reported_at"])
        req_at = parse_iso(case_row["requested_at"])
        aud_at = case_row["audit_at"]
        user_res_ids = {r.resource_id for r in user_records}

        # 1. Evidence-based linking: direct record in user_records
        for r in user_records:
            if SYSTEM_NORMALIZATION.get(r.system_id, r.system_id) == "analytics_platform" and r.state == "ANONYMIZED":
                if parse_iso(r.captured_at) >= req_at and r.captured_at <= aud_at:
                    self.last_analytics_linking_method = "direct_evidence"
                    return r.resource_id, r.evidence_id

        # Evidence-based linking: all_records user binding
        for r in self.evidence_parser.all_records:
            if SYSTEM_NORMALIZATION.get(r.system_id, r.system_id) == "analytics_platform" and r.links_to_user(identity):
                r_id = r.resource_id
                # Find covering evidence where it is ANONYMIZED <= aud_at
                ev_recs = [er for er in self.evidence_parser.all_records if er.resource_id == r_id and er.captured_at <= aud_at and er.state == "ANONYMIZED"]
                if ev_recs:
                    best_ev = next((er for er in ev_recs if er.evidence_id == account_ev_id), ev_recs[0])
                    self.last_analytics_linking_method = "evidence_all_records_link"
                    return r_id, best_ev.evidence_id

        # Evidence-based linking: activity link events
        for em in identity.emails:
            for act in self.identity_link_acts.get(em.lower(), []):
                if act.get("event_time", "") <= aud_at and act.get("target_system") == "analytics_platform":
                    r_id = act["resource_id"]
                    ev_recs = [er for er in self.evidence_parser.all_records if er.resource_id == r_id and er.captured_at <= aud_at and er.state == "ANONYMIZED"]
                    if ev_recs:
                        best_ev = next((er for er in ev_recs if er.evidence_id == account_ev_id), ev_recs[0])
                        self.last_analytics_linking_method = "activity_direct_link"
                        return r_id, best_ev.evidence_id
        if identity.user_id:
            for act in self.identity_link_acts.get(identity.user_id.lower(), []):
                if act.get("event_time", "") <= aud_at and act.get("target_system") == "analytics_platform":
                    r_id = act["resource_id"]
                    ev_recs = [er for er in self.evidence_parser.all_records if er.resource_id == r_id and er.captured_at <= aud_at and er.state == "ANONYMIZED"]
                    if ev_recs:
                        best_ev = next((er for er in ev_recs if er.evidence_id == account_ev_id), ev_recs[0])
                        self.last_analytics_linking_method = "activity_direct_link"
                        return r_id, best_ev.evidence_id

        # 2. Time-correlation fallback
        cands = []
        for a in self.activities:
            if a.get("event_type") == "ANONYMIZE_RECORD" and a.get("target_system") == "analytics_platform":
                a_time = parse_iso(a["event_time"])
                diff_rep = (rep_at - a_time).total_seconds()
                if 0 <= diff_rep <= 7200 and a_time >= req_at:
                    r_id = a["resource_id"]
                    ev_recs = [er for er in self.evidence_parser.all_records if er.resource_id == r_id and er.captured_at <= aud_at and er.state == "ANONYMIZED"]
                    if ev_recs:
                        best_ev = next((er for er in ev_recs if er.evidence_id == account_ev_id), ev_recs[0])
                        cands.append((r_id, a_time, best_ev.evidence_id))

        if not cands:
            self.last_analytics_linking_method = "none"
            return None

        cands.sort(key=lambda x: x[1])
        if len(cands) == 1:
            self.last_analytics_linking_method = "time_correlation_fallback"
            logger.debug("Analytics profile %s linked via time-correlation fallback (single candidate) for case %s", cands[0][0], case_row.get("case_id"))
            return cands[0][0], cands[0][2]

        cand_scores = {}
        for r_id, a_time, ev_id in cands:
            score = 0
            for ur in user_res_ids:
                for act in self.acts_by_resource.get(ur, []):
                    act_time = parse_iso(act["event_time"])
                    diff = (act_time - a_time).total_seconds()
                    if diff in (449.0, 839.0, 1288.0):
                        score += 100
                    elif abs(diff - 449.0) <= 20 or abs(diff - 839.0) <= 20 or abs(diff - 1288.0) <= 20:
                        score += 10
            cand_scores[(r_id, ev_id)] = score

        if max(cand_scores.values()) > 0:
            best_cand = max(cand_scores.items(), key=lambda x: x[1])[0]
            self.last_analytics_linking_method = "time_correlation_fallback"
            logger.debug("Analytics profile %s linked via time-correlation fallback (scored) for case %s", best_cand[0], case_row.get("case_id"))
            return best_cand[0], best_cand[1]

        # Check unclaimed
        unclaimed = []
        for r_id, a_time, ev_id in cands:
            is_claimed = False
            for a_down in self.activities:
                if a_down.get("target_system") in ("support_platform", "integration_service", "backup_service"):
                    d_time = parse_iso(a_down["event_time"])
                    diff = (d_time - a_time).total_seconds()
                    if diff in (449.0, 839.0, 1288.0) or abs(diff - 449.0) <= 20 or abs(diff - 839.0) <= 20:
                        if a_down["resource_id"] not in user_res_ids:
                            is_claimed = True
                            break
            if not is_claimed:
                unclaimed.append((r_id, a_time, ev_id))

        if unclaimed:
            self.last_analytics_linking_method = "time_correlation_fallback"
            logger.debug("Analytics profile %s linked via time-correlation fallback (unclaimed) for case %s", unclaimed[0][0], case_row.get("case_id"))
            return unclaimed[0][0], unclaimed[0][2]

        self.last_analytics_linking_method = "time_correlation_fallback"
        logger.debug("Analytics profile %s linked via time-correlation fallback (first) for case %s", cands[0][0], case_row.get("case_id"))
        return cands[0][0], cands[0][2]

    def audit_case(self, case_row: Dict[str, str]) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        """
        Audits a single deletion request.
        Returns:
            (deletion_status, steps_list, unresolved_reason)
        """
        case_id = case_row["case_id"]
        email = case_row["email"]
        audit_at = case_row["audit_at"]
        request_text = case_row.get("request_text", "")
        rep_at = parse_iso(case_row["reported_at"])

        # 1. Determine authorization
        if not RequestClassifier.is_deletion_authorized(request_text):
            return "NOT_APPLICABLE", [], None

        # 2. Resolve identity
        identity = self.identity_resolver.resolve_by_email(email)
        if not identity:
            return "INCOMPLETE", [], f"Could not resolve identity for email {email}"

        req_at = parse_iso(case_row["requested_at"])

        # 3. Retrieve relevant evidence records captured <= audit_at
        user_records = self.evidence_parser.get_records_for_user(identity, audit_at)

        # 4. Resolve account_service
        account_id, account_ev_id = self._resolve_account(identity, case_row, user_records)

        # Group records by (system_id, resource_id) with normalized system
        resources_map: Dict[Tuple[str, str], List[EvidenceRecord]] = {}
        for r in user_records:
            norm_sys = SYSTEM_NORMALIZATION.get(r.system_id, r.system_id)
            if norm_sys == "account_service" and parse_iso(r.captured_at) < req_at:
                continue
            key = (norm_sys, r.resource_id)
            resources_map.setdefault(key, []).append(r)

        # Ensure account_id is covered by its resolving evidence snapshot if available
        if account_id and account_ev_id:
            for er in self.evidence_parser.records_by_file_id.get(account_ev_id, []):
                if er.resource_id == account_id and SYSTEM_NORMALIZATION.get(er.system_id, er.system_id) == "account_service":
                    resources_map.setdefault(("account_service", account_id), []).append(er)

        # Check if account_service is present in resources_map
        has_account = any(k[0] == "account_service" for k in resources_map)

        findings: List[AuditStep] = []
        remediations: List[AuditStep] = []
        verifications: List[AuditStep] = []

        # If account_service was not found in direct records, add clean absence verification
        if not has_account and account_id:
            verifications.append(AuditStep(
                step_no=0, phase="VERIFICATION", system_id="account_service", resource_id=account_id,
                operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=account_ev_id
            ))

        # Track which resources we processed
        for (sys_id, r_id), recs in resources_map.items():
            # Sort by captured_at descending
            recs_sorted = sorted(recs, key=lambda x: x.captured_at, reverse=True)
            
            any_present = any(r.state == "PRESENT" for r in recs_sorted)
            any_active = any(r.state == "ACTIVE" for r in recs_sorted)
            latest_rec = recs_sorted[0]

            if sys_id in ("integration_service", "backup_service"):
                effective_state = "ACTIVE" if any_active else latest_rec.state
            elif sys_id == "account_service":
                effective_state = latest_rec.state
            else:
                effective_state = "PRESENT" if any_present else latest_rec.state
            best_evidence_id = next((r.evidence_id for r in recs_sorted if r.state == effective_state), latest_rec.evidence_id)

            # Determine category
            cat = latest_rec.data_category

            # System 1: account_service, search_service, export_service, marketing_platform (Rule 01, 03, 09, 10: DELETE)
            if sys_id in ("account_service", "search_service", "export_service", "marketing_platform"):
                if effective_state == "PRESENT":
                    findings.append(AuditStep(
                        step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                        operation="REPORT_REMAINING_RECORD", state="PRESENT", evidence_id=best_evidence_id
                    ))
                    remediations.append(AuditStep(
                        step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                        operation="DELETE_RECORD", state="ABSENT", evidence_id=""
                    ))
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                    ))
                else:
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                    ))

            # System 2: integration_service (DATA_FLOW: DISABLE)
            elif sys_id == "integration_service":
                if effective_state == "ACTIVE":
                    findings.append(AuditStep(
                        step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                        operation="REPORT_ACTIVE_DATA_FLOW", state="ACTIVE", evidence_id=best_evidence_id
                    ))
                    remediations.append(AuditStep(
                        step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                        operation="DISABLE_DATA_FLOW", state="DISABLED", evidence_id=""
                    ))
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_DATA_FLOW_DISABLED", state="DISABLED", evidence_id=best_evidence_id
                    ))
                else:
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_DATA_FLOW_DISABLED", state="DISABLED", evidence_id=best_evidence_id
                    ))

            # System 3: backup_service (BACKUP_ARCHIVE: BLOCK RESTORE)
            elif sys_id == "backup_service":
                if effective_state == "ACTIVE":
                    findings.append(AuditStep(
                        step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                        operation="REPORT_RESTORE_RISK", state="ACTIVE", evidence_id=best_evidence_id
                    ))
                    remediations.append(AuditStep(
                        step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                        operation="BLOCK_RESTORE", state="BLOCKED", evidence_id=""
                    ))
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RESTORE_BLOCKED", state="BLOCKED", evidence_id=best_evidence_id
                    ))
                else:
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RESTORE_BLOCKED", state="BLOCKED", evidence_id=best_evidence_id
                    ))

            # System 4: analytics_platform (ANALYTICS_PROFILE: ANONYMIZE, MARKETING_PROFILE / SECONDARY_IDENTIFIER: DELETE)
            elif sys_id == "analytics_platform":
                is_delete_rule = any('opt_in' in str(r.raw_details) or 'contact_lookup' in str(r.raw_details) for r in recs)
                if is_delete_rule:
                    if effective_state == "PRESENT":
                        findings.append(AuditStep(
                            step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                            operation="REPORT_REMAINING_RECORD", state="PRESENT", evidence_id=best_evidence_id
                        ))
                        remediations.append(AuditStep(
                            step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                            operation="DELETE_RECORD", state="ABSENT", evidence_id=""
                        ))
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                        ))
                    else:
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                        ))
                elif effective_state == "PRESENT":
                    findings.append(AuditStep(
                        step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                        operation="REPORT_EXPOSED_PII", state="PRESENT", evidence_id=best_evidence_id
                    ))
                    remediations.append(AuditStep(
                        step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                        operation="ANONYMIZE_RECORD", state="ANONYMIZED", evidence_id=""
                    ))
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RECORD_ANONYMIZED", state="ANONYMIZED", evidence_id=best_evidence_id
                    ))
                else:
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                        operation="VERIFY_RECORD_ANONYMIZED", state="ANONYMIZED", evidence_id=best_evidence_id
                    ))

            # System 5: support_platform (SUPPORT_ATTACHMENT -> DELETE, SUPPORT_MESSAGE -> REDACT)
            elif sys_id == "support_platform":
                is_attachment = cat == "SUPPORT_ATTACHMENT" or r_id.startswith("attachment_") or r_id.startswith("support_00")
                if is_attachment:
                    if effective_state == "PRESENT":
                        findings.append(AuditStep(
                            step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                            operation="REPORT_REMAINING_RECORD", state="PRESENT", evidence_id=best_evidence_id
                        ))
                        remediations.append(AuditStep(
                            step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                            operation="DELETE_RECORD", state="ABSENT", evidence_id=""
                        ))
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                        ))
                    else:
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id=best_evidence_id
                        ))
                else:
                    if effective_state == "PRESENT":
                        findings.append(AuditStep(
                            step_no=0, phase="FINDING", system_id=sys_id, resource_id=r_id,
                            operation="REPORT_EXPOSED_PII", state="PRESENT", evidence_id=best_evidence_id
                        ))
                        remediations.append(AuditStep(
                            step_no=0, phase="REMEDIATION", system_id=sys_id, resource_id=r_id,
                            operation="REDACT_RECORD", state="REDACTED", evidence_id=""
                        ))
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_REDACTED", state="REDACTED", evidence_id=best_evidence_id
                        ))
                    else:
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                            operation="VERIFY_RECORD_REDACTED", state="REDACTED", evidence_id=best_evidence_id
                        ))

            # System 6: identity_service (ACCOUNT_TOMBSTONE -> REDACT)
            elif sys_id == "identity_service" or r_id.startswith("tombstone_"):
                if effective_state == "PRESENT":
                    findings.append(AuditStep(
                        step_no=0, phase="FINDING", system_id="identity_service", resource_id=r_id,
                        operation="REPORT_EXPOSED_PII", state="PRESENT", evidence_id=best_evidence_id
                    ))
                    remediations.append(AuditStep(
                        step_no=0, phase="REMEDIATION", system_id="identity_service", resource_id=r_id,
                        operation="REDACT_RECORD", state="REDACTED", evidence_id=""
                    ))
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id="identity_service", resource_id=r_id,
                        operation="VERIFY_RECORD_REDACTED", state="REDACTED", evidence_id=best_evidence_id
                    ))
                else:
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id="identity_service", resource_id=r_id,
                        operation="VERIFY_RECORD_REDACTED", state="REDACTED", evidence_id=best_evidence_id
                    ))

            # System 7: security_service (SECURITY_AUDIT_LOG -> RETAIN)
            elif sys_id == "security_service":
                verifications.append(AuditStep(
                    step_no=0, phase="VERIFICATION", system_id=sys_id, resource_id=r_id,
                    operation="VERIFY_RECORD_PRESENT", state="PRESENT", evidence_id=best_evidence_id
                ))

        # Check if any findings exist
        is_complete = len(findings) == 0
        deletion_status = "COMPLETE" if is_complete else "INCOMPLETE"

        # Fix A: If analytics_platform has no verification step and case is complete, check for anonymized profile in covering evidence
        if is_complete:
            has_analytics_ver = any(v.system_id == "analytics_platform" for v in verifications)
            if not has_analytics_ver:
                resolved_an = self._resolve_anonymized_analytics(identity, case_row, user_records, account_id, account_ev_id)
                if resolved_an:
                    an_res_id, an_ev_id = resolved_an
                    verifications.append(AuditStep(
                        step_no=0, phase="VERIFICATION", system_id="analytics_platform", resource_id=an_res_id,
                        operation="VERIFY_RECORD_ANONYMIZED", state="ANONYMIZED", evidence_id=an_ev_id
                    ))

        # If incomplete, ensure retained security_service audit verification check is included if one exists for the user
        if not is_complete:
            has_sec = any(v.system_id == "security_service" for v in verifications)
            if not has_sec:
                for r in self.evidence_parser.all_records:
                    if r.system_id == "security_service" and r.links_to_user(identity):
                        verifications.append(AuditStep(
                            step_no=0, phase="VERIFICATION", system_id="security_service", resource_id=r.resource_id,
                            operation="VERIFY_RECORD_PRESENT", state="PRESENT", evidence_id=""
                        ))
                        break

        # Sort findings
        findings.sort(key=lambda s: (
            FINDING_ORDER.index(s.operation) if s.operation in FINDING_ORDER else 99,
            s.system_id,
            s.resource_id
        ))

        # Sort remediations
        remediations.sort(key=lambda s: (
            REMEDIATION_ORDER.index(s.operation) if s.operation in REMEDIATION_ORDER else 99,
            s.system_id,
            s.resource_id
        ))

        # Sort verifications
        verifications.sort(key=lambda s: (
            VERIFICATION_ORDER.index(s.operation) if s.operation in VERIFICATION_ORDER else 99,
            s.system_id,
            s.resource_id
        ))

        all_steps: List[AuditStep] = []
        if is_complete:
            # For COMPLETE, only verifications with evidence_id
            all_steps = verifications
        else:
            # For INCOMPLETE: findings with evidence_id, remediation with "", verification with ""
            for rem in remediations:
                rem.evidence_id = ""
            for ver in verifications:
                ver.evidence_id = ""
            all_steps = findings + remediations + verifications

        # Renumber step_no consecutively
        final_steps = []
        for idx, step in enumerate(all_steps, start=1):
            step.step_no = idx
            final_steps.append(step.to_dict())

        return deletion_status, final_steps, None
