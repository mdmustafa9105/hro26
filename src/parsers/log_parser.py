import os
import re
import json
from typing import List, Dict, Any
from src.models import EvidenceRecord

def parse_log_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    traces: Dict[str, Dict[str, Any]] = {}

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]

    # First pass: collect trace info from ALL lines (JSON or key=value)
    for line in lines:
        t_id = None
        # Check JSON first
        json_start = line.find('{')
        json_end = line.rfind('}')
        if json_start != -1 and json_end > json_start:
            try:
                d = json.loads(line[json_start:json_end+1])
                t_id = d.get('trace_id') or d.get('requestId')
                if t_id:
                    t_data = traces.setdefault(str(t_id), {})
                    if d.get('resource_id'):
                        t_data['resource_id'] = d.get('resource_id')
                    if d.get('service') or d.get('system'):
                        t_data['service'] = d.get('service') or d.get('system')

                    # Subject / User ref
                    for k in ('subject_ref', 'subject_reference', 'user_id', 'customer_reference', 'lookup_key', 'correlation_key', 'subject_key'):
                        val = d.get(k)
                        if val and str(val).lower().startswith('user_'):
                            t_data['user_id'] = str(val).lower()
                            t_data['subject_reference'] = str(val).lower()
                            t_data['customer_reference'] = str(val).lower()
                            break

                    # Email
                    for k in ('email', 'lookup_key', 'requester_email', 'customer_email', 'matched_value', 'correlation_key', 'subject_key'):
                        val = d.get(k)
                        if val and '@' in str(val):
                            t_data['email'] = str(val).lower()
                            break

                    # Email hash
                    for k in ('email_hash', 'lookup_key', 'correlation_key'):
                        val = str(d.get(k, ''))
                        if len(val) == 64 and all(c in '0123456789abcdefABCDEF' for c in val):
                            t_data['email_hash'] = val.lower()
                            break

                    # Phone
                    for k in ('phone', 'requester_phone', 'matched_value'):
                        val = d.get(k)
                        if val:
                            t_data['phone'] = str(val)
                            break
            except Exception:
                pass

        # Also check regex for key=value lines or embedded trace_ids
        if not t_id:
            t_match = re.search(r'["\']?trace_id["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)', line, re.I)
            if not t_match:
                t_match = re.search(r'requestId=([a-zA-Z0-9_\-]+)', line, re.I)
            if t_match:
                t_id = t_match.group(1)
                t_data = traces.setdefault(t_id, {})

                r_match = re.search(r'resource_id=([a-zA-Z0-9_\-]+)', line)
                if r_match:
                    t_data['resource_id'] = r_match.group(1)

                s_match = re.search(r'service=([a-zA-Z0-9_\-]+)', line)
                if s_match:
                    t_data['service'] = s_match.group(1)

                e_match = re.search(r'\b(?:email|lookup_key|requester_email|customer_email|correlation_key|subject_key|matched_value)=(?:")?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?:")?', line, re.I)
                if e_match:
                    t_data['email'] = e_match.group(1).lower()

                h_match = re.search(r'\b(?:email_hash|lookup_key|correlation_key)=(?:")?([a-fA-F0-9]{64})(?:")?', line)
                if h_match:
                    t_data['email_hash'] = h_match.group(1).lower()

                u_match = re.search(r'\b(?:lookup_key|correlation_key|subject_reference|subject_ref|subject_key|customer_reference)=(?:")?(user_\d+)(?:")?', line, re.I)
                if u_match:
                    uid = u_match.group(1).lower()
                    t_data['user_id'] = uid
                    t_data['subject_reference'] = uid
                    t_data['customer_reference'] = uid

                p_match = re.search(r'\b(?:phone|requester_phone|lookup_key|matched_value)=(?:")?(\+?[\d\s\-]{8,}\d)(?:")?', line)
                if p_match:
                    t_data['phone'] = p_match.group(1)

    # Second pass: parse records and attach correlated trace info
    for line in lines:
        # Case A: JSON structured log line
        json_start = line.find('{')
        json_end = line.rfind('}')
        if json_start != -1 and json_end > json_start:
            try:
                d = json.loads(line[json_start:json_end+1])
                t_id = d.get('trace_id') or d.get('requestId')
                t_info = traces.get(str(t_id), {}) if t_id else {}

                r_id = d.get('resource_id') or t_info.get('resource_id')
                if r_id:
                    sys_id = d.get('service') or d.get('system') or t_info.get('service') or 'account_service'
                    state = 'PRESENT'
                    if d.get('status_code') == 404 or d.get('rows') == 0 or d.get('rows') == '0' or d.get('http_status') == 404:
                        state = 'ABSENT'
                    elif d.get('enabled') is False or str(d.get('enabled')).lower() in ('false', '0', 'disabled'):
                        state = 'DISABLED'
                    elif d.get('enabled') is True or str(d.get('enabled')).lower() in ('true', '1', 'active'):
                        state = 'ACTIVE'
                    elif d.get('result') in ('DISABLED', 'disabled') or d.get('status') in ('DISABLED', 'disabled'):
                        state = 'DISABLED'
                    elif d.get('result') in ('ACTIVE', 'active') or d.get('status') in ('ACTIVE', 'active'):
                        state = 'ACTIVE'
                    elif d.get('restore_allowed') is False or str(d.get('restore_allowed')).lower() in ('false', '0', 'blocked'):
                        state = 'BLOCKED'
                    elif d.get('restore_allowed') is True or str(d.get('restore_allowed')).lower() in ('true', '1', 'active'):
                        state = 'ACTIVE'

                    email = d.get('email') or d.get('lookup_key') or d.get('correlation_key') or t_info.get('email')
                    if email and '@' not in str(email):
                        email = t_info.get('email')

                    email_hash = d.get('email_hash')
                    for k in ('correlation_key', 'lookup_key'):
                        val = str(d.get(k, ''))
                        if len(val) == 64 and all(c in '0123456789abcdefABCDEF' for c in val):
                            email_hash = val.lower()
                    if not email_hash:
                        email_hash = t_info.get('email_hash')

                    user_id = d.get('user_id') or d.get('subject_ref') or d.get('subject_reference') or d.get('customer_reference') or d.get('correlation_key')
                    if user_id and str(user_id).startswith('user_'):
                        user_id = str(user_id).lower()
                    else:
                        user_id = t_info.get('user_id')

                    cust_ref = d.get('customer_reference') or t_info.get('customer_reference') or user_id
                    subj_ref = d.get('subject_reference') or d.get('subject_ref') or t_info.get('subject_reference') or user_id
                    phone = d.get('phone') or t_info.get('phone')

                    data_cat = 'USER_PROFILE'
                    if sys_id == 'search_service':
                        data_cat = 'SEARCH_INDEX_ENTRY'
                    elif sys_id == 'analytics_platform':
                        data_cat = 'ANALYTICS_PROFILE'
                    elif sys_id in ('support_platform', 'support_replica'):
                        if str(r_id).startswith('support_00') or str(r_id).startswith('attachment_'):
                            data_cat = 'SUPPORT_ATTACHMENT'
                        else:
                            data_cat = 'SUPPORT_MESSAGE'
                    elif sys_id in ('backup_service', 'backup_restore_service'):
                        data_cat = 'BACKUP_ARCHIVE'
                    elif sys_id in ('integration_service', 'integration_admin'):
                        data_cat = 'DATA_FLOW'
                    elif sys_id == 'security_service':
                        data_cat = 'SECURITY_AUDIT_LOG'
                    elif sys_id == 'export_service':
                        data_cat = 'USER_EXPORT'
                    elif sys_id == 'identity_service':
                        data_cat = 'ACCOUNT_TOMBSTONE'

                    records.append(EvidenceRecord(
                        evidence_id=file_id,
                        file_path=file_path,
                        captured_at=captured_at,
                        origin=origin,
                        system_id=sys_id,
                        resource_id=r_id,
                        data_category=data_cat,
                        state=state,
                        user_id=user_id,
                        customer_reference=cust_ref,
                        subject_reference=subj_ref,
                        email=email.lower() if email else None,
                        email_hash=email_hash,
                        phone=phone,
                        name=d.get('name') or d.get('display_name'),
                        raw_details=d
                    ))
            except Exception:
                pass
            continue

        # Case B: Key=Value trace line
        # Skip started lines and noise events, only parse completed or evaluation lines
        if any(k in line for k in ['_started', 'connection_acquired', 'dependency_retry', 'dependency_recovered', 'lease_extended', 'consumer_lag']):
            continue

        r_match = re.search(r'\bresource_id=([a-zA-Z0-9_\-]+)', line)
        t_match = re.search(r'["\']?trace_id["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)', line, re.I)
        if not t_match:
            t_match = re.search(r'requestId=([a-zA-Z0-9_\-]+)', line, re.I)

        t_id = t_match.group(1) if t_match else None
        t_info = traces.get(t_id, {}) if t_id else {}

        r_id = r_match.group(1) if r_match else t_info.get('resource_id')
        if not r_id:
            continue

        s_match = re.search(r'\bservice=([a-zA-Z0-9_\-]+)', line)
        sys_id = s_match.group(1) if s_match else (t_info.get('service') or origin)

        # Email
        email = t_info.get('email')
        e_match = re.search(r'\b(?:email|lookup_key|requester_email|customer_email|correlation_key|subject_key|matched_value)=(?:")?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?:")?', line, re.I)
        if e_match:
            email = e_match.group(1).lower()

        # Email hash
        email_hash = t_info.get('email_hash')
        h_match = re.search(r'\b(?:email_hash|lookup_key|correlation_key)=(?:")?([a-fA-F0-9]{64})(?:")?', line)
        if h_match:
            email_hash = h_match.group(1).lower()

        # User id / correlation key / subject reference
        user_id = t_info.get('user_id')
        u_match = re.search(r'\b(?:lookup_key|correlation_key|subject_reference|subject_ref|subject_key|customer_reference)=(?:")?(user_\d+)(?:")?', line, re.I)
        if u_match:
            user_id = u_match.group(1).lower()

        # Phone
        phone = t_info.get('phone')
        p_match = re.search(r'\b(?:phone|requester_phone|lookup_key|matched_value)=(?:")?(\+?[\d\s\-]{8,}\d)(?:")?', line)
        if p_match:
            phone = p_match.group(1)

        # Customer reference
        cust_ref = t_info.get('user_id')
        c_match = re.search(r'\bcustomer_reference=(?:")?([a-zA-Z0-9_\-]+)(?:")?', line)
        if c_match and c_match.group(1) != 'null':
            cust_ref = c_match.group(1)

        # Determine state
        state = 'PRESENT'
        clean_line = line.replace('"', '').replace("'", "")
        if 'http_status=404' in clean_line or 'rows=0' in clean_line or 'total_hits=0' in clean_line or 'status=NOT_FOUND' in clean_line:
            state = 'ABSENT'
        elif any(k in clean_line for k in ('enabled=true', 'enabled=1', 'status=ACTIVE', 'result=ACTIVE', 'remains enabled', 'is active')):
            state = 'ACTIVE'
        elif any(k in clean_line for k in ('enabled=false', 'enabled=0', 'status=DISABLED', 'result=DISABLED', 'flow disabled', 'connector stopped')):
            state = 'DISABLED'
        elif any(k in clean_line for k in ('restore_allowed=false', 'status=BLOCKED', 'deletion_block=true')):
            state = 'BLOCKED'
        elif any(k in clean_line for k in ('restore_allowed=true', 'deletion_block=false')):
            state = 'ACTIVE'
        elif 'marker_found=false' in clean_line:
            state = 'PRESENT'
        elif 'marker_found=true' in clean_line:
            state = 'ABSENT'
        elif sys_id == 'analytics_platform' and ('ANONYMIZED' in clean_line or 'no direct identifier' in clean_line or 'email=null' in clean_line):
            if 'email=null' in clean_line and 'customer_reference=null' in clean_line:
                state = 'ANONYMIZED'
        elif r_id.startswith('tombstone_') and ('REDACTED' in clean_line or 'pii=none' in clean_line or 'email=null' in clean_line):
            state = 'REDACTED'

        data_cat = 'USER_PROFILE'
        if sys_id == 'search_service':
            data_cat = 'SEARCH_INDEX_ENTRY'
        elif sys_id == 'analytics_platform':
            data_cat = 'ANALYTICS_PROFILE'
        elif sys_id in ('support_platform', 'support_replica'):
            if r_id.startswith('support_00') or r_id.startswith('attachment_'):
                data_cat = 'SUPPORT_ATTACHMENT'
            else:
                data_cat = 'SUPPORT_MESSAGE'
        elif sys_id in ('backup_service', 'backup_restore_service'):
            data_cat = 'BACKUP_ARCHIVE'
        elif sys_id in ('integration_service', 'integration_admin'):
            data_cat = 'DATA_FLOW'
        elif sys_id == 'security_service':
            data_cat = 'SECURITY_AUDIT_LOG'
        elif sys_id == 'export_service':
            data_cat = 'USER_EXPORT'
        elif sys_id == 'identity_service':
            data_cat = 'ACCOUNT_TOMBSTONE'

        records.append(EvidenceRecord(
            evidence_id=file_id,
            file_path=file_path,
            captured_at=captured_at,
            origin=origin,
            system_id=sys_id,
            resource_id=r_id,
            data_category=data_cat,
            state=state,
            user_id=user_id,
            customer_reference=cust_ref,
            subject_reference=cust_ref or user_id,
            email=email,
            email_hash=email_hash,
            phone=phone,
            raw_details={'line': line}
        ))

    return records
