import json
import os
from typing import List
from src.models import EvidenceRecord

def parse_json_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return records

    # Format 1: Snapshot bundles {'snapshots': [{'data_store': ..., 'collection': ..., 'records': [...]}]}
    if 'snapshots' in data:
        for snap in data.get('snapshots', []):
            store = snap.get('data_store', '')
            coll = snap.get('collection', '')
            snap_records = snap.get('records', [])

            for rec in snap_records:
                if not isinstance(rec, dict):
                    continue
                r_id = rec.get('resource_id')
                if not r_id:
                    continue

                sys_id = store
                data_cat = 'USER_PROFILE'
                state = 'PRESENT'

                if sys_id == 'account_service':
                    data_cat = 'USER_PROFILE'
                    state = 'PRESENT'
                elif sys_id == 'identity_service' or r_id.startswith('tombstone_'):
                    sys_id = 'identity_service'
                    data_cat = 'ACCOUNT_TOMBSTONE'
                    has_pii = any(rec.get(k) for k in ('name', 'email', 'phone', 'email_hash'))
                    state = 'PRESENT' if has_pii else 'REDACTED'
                elif sys_id == 'search_service':
                    data_cat = 'SEARCH_INDEX_ENTRY'
                    state = 'PRESENT'
                elif sys_id == 'analytics_platform':
                    data_cat = 'ANALYTICS_PROFILE'
                    has_id = any(rec.get(k) for k in ('user_id', 'email', 'phone', 'email_hash', 'customer_reference'))
                    state = 'PRESENT' if has_id else 'ANONYMIZED'
                elif sys_id == 'support_platform':
                    if 'ticket_attachments' in coll or r_id.startswith('attachment_'):
                        data_cat = 'SUPPORT_ATTACHMENT'
                        state = 'PRESENT'
                    else:
                        data_cat = 'SUPPORT_MESSAGE'
                        has_pii = any(rec.get(k) for k in ('requester_name', 'requester_email', 'requester_phone', 'email', 'phone', 'name'))
                        state = 'PRESENT' if has_pii else 'REDACTED'
                elif sys_id == 'export_service':
                    data_cat = 'USER_EXPORT'
                    state = 'PRESENT'
                elif sys_id == 'integration_service':
                    data_cat = 'DATA_FLOW'
                    val = rec.get('enabled')
                    if val is None:
                        val = rec.get('status')
                    if val is None:
                        val = rec.get('state')
                    is_active = val in (True, 1, 'ACTIVE', 'true') or str(val).lower() in ('true', '1', 'active')
                    state = 'ACTIVE' if is_active else 'DISABLED'
                elif sys_id == 'backup_service':
                    data_cat = 'BACKUP_ARCHIVE'
                    restore_allowed = rec.get('restore_allowed') in (True, 1, 'ACTIVE', 'true')
                    state = 'ACTIVE' if restore_allowed else 'BLOCKED'
                elif sys_id == 'security_service':
                    data_cat = 'SECURITY_AUDIT_LOG'
                    state = 'PRESENT'

                sel = rec.get('subject_selector')
                sel_email = str(sel).lower() if sel and '@' in str(sel) else None
                sel_user_id = str(sel).lower() if sel and str(sel).lower().startswith('user_') else None

                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id=sys_id,
                    resource_id=r_id,
                    data_category=data_cat,
                    state=state,
                    user_id=rec.get('user_id') or sel_user_id,
                    customer_reference=rec.get('customer_reference') or (sel if not sel_email else None),
                    subject_reference=rec.get('subject_reference') or sel,
                    email=rec.get('email') or rec.get('owner_email') or rec.get('customer_email') or rec.get('requester_email') or sel_email,
                    phone=rec.get('phone') or rec.get('owner_phone') or rec.get('requester_phone'),
                    email_hash=rec.get('email_hash'),
                    name=rec.get('name') or rec.get('full_name') or rec.get('display_name') or rec.get('uploaded_by'),
                    raw_details=rec
                ))

    # Format 2: Service exports {'service_exports': {'account_service': {...}, ...}}
    elif 'service_exports' in data:
        for sys_id, content in data.get('service_exports', {}).items():
            if not isinstance(content, dict):
                continue
            for list_name, items in content.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    r_id = item.get('resource_id')
                    if not r_id:
                        continue

                    data_cat = 'USER_PROFILE'
                    state = 'PRESENT'

                    if sys_id == 'account_service':
                        data_cat = 'USER_PROFILE'
                        status_code = item.get('status_code')
                        profile = item.get('profile')
                        if status_code == 404 or profile is None:
                            state = 'ABSENT'
                        else:
                            state = 'PRESENT'
                    elif sys_id == 'analytics_platform':
                        data_cat = 'ANALYTICS_PROFILE'
                        has_id = any(item.get(k) for k in ('email', 'phone', 'email_hash', 'customer_reference'))
                        state = 'PRESENT' if has_id else 'ANONYMIZED'
                    elif sys_id == 'backup_service':
                        data_cat = 'BACKUP_ARCHIVE'
                        restore_allowed = item.get('restore_allowed') in (True, 1, 'ACTIVE', 'true')
                        state = 'ACTIVE' if restore_allowed else 'BLOCKED'
                    elif sys_id == 'export_service':
                        data_cat = 'USER_EXPORT'
                        state = 'PRESENT'
                    elif sys_id == 'integration_service':
                        data_cat = 'DATA_FLOW'
                        val = item.get('enabled')
                        if val is None:
                            val = item.get('status')
                        if val is None:
                            val = item.get('state')
                        enabled = val in (True, 1, 'ACTIVE', 'true') or str(val).lower() in ('true', '1', 'active')
                        state = 'ACTIVE' if enabled else 'DISABLED'
                    elif sys_id == 'search_service':
                        data_cat = 'SEARCH_INDEX_ENTRY'
                        hits = item.get('hits')
                        if isinstance(hits, dict):
                            docs = hits.get('documents', [])
                            if not docs and hits.get('total', 0) == 0:
                                state = 'ABSENT'
                            else:
                                state = 'PRESENT'
                        elif isinstance(hits, list):
                            if not hits and item.get('total_hits', 0) == 0:
                                state = 'ABSENT'
                            else:
                                state = 'PRESENT'
                    elif sys_id == 'security_service':
                        data_cat = 'SECURITY_AUDIT_LOG'
                        state = 'PRESENT'
                    elif sys_id == 'support_platform':
                        data_cat = 'SUPPORT_MESSAGE'
                        has_pii = any(item.get(k) for k in ('requester_name', 'requester_email', 'requester_phone', 'email', 'phone', 'name'))
                        state = 'PRESENT' if has_pii else 'REDACTED'

                    sel = item.get('subject_selector')
                    sel_email = str(sel).lower() if sel and '@' in str(sel) else None
                    sel_user_id = str(sel).lower() if sel and str(sel).lower().startswith('user_') else None

                    email = item.get('email') or item.get('owner_email') or item.get('customer_email') or item.get('requester_email') or sel_email
                    phone = item.get('phone') or item.get('owner_phone') or item.get('requester_phone')
                    name = item.get('requester_name') or item.get('name') or item.get('full_name')
                    user_id = item.get('user_id') or sel_user_id or (item.get('customer_reference') if str(item.get('customer_reference', '')).startswith('user_') else None) or (item.get('subject_reference') if str(item.get('subject_reference', '')).startswith('user_') else None)
                    customer_reference = item.get('customer_reference') or (sel if not sel_email else None)
                    subject_reference = item.get('subject_reference') or item.get('customer_reference') or sel
                    email_hash = item.get('email_hash')

                    # Deep unpack profile if present (e.g. account_service profile_lookups)
                    profile = item.get('profile')
                    if isinstance(profile, dict):
                        if not email:
                            email = profile.get('email')
                        if not phone:
                            phone = profile.get('phone')
                        if not name:
                            name = profile.get('full_name')
                        if not customer_reference:
                            customer_reference = profile.get('customer_reference')
                        if not email_hash:
                            email_hash = profile.get('email_hash')
                        if not user_id and customer_reference and str(customer_reference).startswith('user_'):
                            user_id = customer_reference

                    # Deep unpack search hits/query (e.g. search_service index_queries)
                    query = item.get('query')
                    if query:
                        if '@' in query and not email:
                            email = query
                        elif query.startswith('user_') and not user_id:
                            user_id = query

                    hits = item.get('hits')
                    if isinstance(hits, dict):
                        docs = hits.get('documents', [])
                        for doc in docs:
                            if isinstance(doc, dict):
                                if not email and doc.get('email'):
                                    email = doc.get('email')
                                if not phone and doc.get('phone'):
                                    phone = doc.get('phone')
                                if not name and doc.get('display_name'):
                                    name = doc.get('display_name')
                                if not customer_reference and doc.get('customer_reference'):
                                    customer_reference = doc.get('customer_reference')
                                if not email_hash and doc.get('email_hash'):
                                    email_hash = doc.get('email_hash')
                                if not user_id and customer_reference and str(customer_reference).startswith('user_'):
                                    user_id = customer_reference

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
                        customer_reference=customer_reference,
                        subject_reference=subject_reference,
                        email=email,
                        phone=phone,
                        email_hash=email_hash,
                        name=name,
                        raw_details=item
                    ))

    # Format 3 & 4: Top-level records {'records': [...]} (e.g. connector configs or analytics reports)
    elif 'records' in data:
        for rec in data.get('records', []):
            if not isinstance(rec, dict):
                continue
            r_id = rec.get('resource_id')
            if not r_id:
                continue

            sys_id = rec.get('system') or origin or 'account_service'
            data_cat = rec.get('record_type') or 'USER_PROFILE'
            state = 'PRESENT'

            res = rec.get('result')
            if res == 'NOT_FOUND' or res == 'ABSENT':
                state = 'ABSENT'
            elif sys_id == 'analytics_platform' or 'analytics' in str(origin):
                sys_id = 'analytics_platform'
                data_cat = 'ANALYTICS_PROFILE'
                has_id = any(rec.get(k) for k in ('user_id', 'email', 'phone', 'email_hash', 'customer_reference'))
                state = 'PRESENT' if has_id else 'ANONYMIZED'
            elif sys_id == 'integration_service' or 'connector' in str(origin):
                sys_id = 'integration_service'
                data_cat = 'DATA_FLOW'
                enabled = rec.get('enabled') in (True, 1, 'ACTIVE', 'true')
                state = 'ACTIVE' if enabled else 'DISABLED'

            records.append(EvidenceRecord(
                evidence_id=file_id,
                file_path=file_path,
                captured_at=captured_at,
                origin=origin,
                system_id=sys_id,
                resource_id=r_id,
                data_category=data_cat,
                state=state,
                user_id=rec.get('user_id'),
                customer_reference=rec.get('customer_reference'),
                subject_reference=rec.get('subject_reference'),
                email=rec.get('email') or rec.get('owner_email') or rec.get('customer_email'),
                phone=rec.get('phone'),
                email_hash=rec.get('email_hash'),
                name=rec.get('name') or rec.get('full_name'),
                raw_details=rec
            ))

    return records
