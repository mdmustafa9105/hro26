import sqlite3
import json
import os
from typing import List
from src.models import EvidenceRecord

def parse_sql_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        sql = f.read()

    db = sqlite3.connect(':memory:')
    try:
        db.executescript(sql)
    except Exception as e:
        db.close()
        return records

    cursor = db.cursor()
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    for table in tables:
        # 1. Direct replica tables (JSON payloads)
        if table in ('customer_data_primary', 'customer_data_failover_replica', 'customer_data_read_replica',
                     'customer_data_reporting_replica', 'customer_data_replica_ap_south', 'customer_data_replica_eu_west'):
            rows = cursor.execute(f"SELECT resource_id, origin_system, collection_name, record_json FROM {table}").fetchall()
            for r_id, orig_sys, coll_name, rec_json in rows:
                rec_data = {}
                if rec_json:
                    try:
                        rec_data = json.loads(rec_json)
                    except Exception:
                        pass
                
                # Determine data category and state
                sys_id = orig_sys or 'account_service'
                data_cat = 'USER_PROFILE'
                state = 'PRESENT'

                if sys_id == 'identity_service' or r_id.startswith('tombstone_'):
                    sys_id = 'identity_service'
                    data_cat = 'ACCOUNT_TOMBSTONE'
                    # Check if PII is redacted
                    has_pii = any(rec_data.get(k) for k in ('name', 'email', 'phone', 'email_hash'))
                    state = 'PRESENT' if has_pii else 'REDACTED'
                elif sys_id == 'analytics_platform':
                    data_cat = 'ANALYTICS_PROFILE'
                    has_id = any(rec_data.get(k) for k in ('user_id', 'email', 'phone', 'email_hash', 'customer_reference'))
                    state = 'PRESENT' if has_id else 'ANONYMIZED'
                elif sys_id == 'security_service':
                    data_cat = 'SECURITY_AUDIT_LOG'
                    state = 'PRESENT'
                elif sys_id == 'backup_service':
                    data_cat = 'BACKUP_ARCHIVE'
                    restore_allowed = rec_data.get('restore_allowed', True)
                    state = 'ACTIVE' if restore_allowed in (True, 1, 'ACTIVE', 'true') else 'BLOCKED'
                elif sys_id == 'integration_service':
                    data_cat = 'DATA_FLOW'
                    enabled = rec_data.get('enabled', True)
                    state = 'ACTIVE' if enabled in (True, 1, 'ACTIVE', 'true') else 'DISABLED'
                elif sys_id == 'search_service':
                    data_cat = 'SEARCH_INDEX_ENTRY'
                    state = 'PRESENT'
                elif sys_id == 'support_platform':
                    data_cat = 'SUPPORT_MESSAGE'
                    state = 'PRESENT'
                elif sys_id == 'export_service':
                    data_cat = 'USER_EXPORT'
                    state = 'PRESENT'

                # Unpack nested document or profile if present
                doc = rec_data.get('document') or rec_data.get('profile') or {}
                if not isinstance(doc, dict):
                    doc = {}

                user_id = rec_data.get('user_id') or doc.get('user_id')
                cust_ref = rec_data.get('customer_reference') or doc.get('customer_reference')
                subj_ref = rec_data.get('subject_reference') or doc.get('subject_reference')
                email = (rec_data.get('email') or rec_data.get('owner_email') or 
                         rec_data.get('customer_email') or rec_data.get('requester_email') or 
                         doc.get('email') or doc.get('customer_email'))
                phone = (rec_data.get('phone') or rec_data.get('owner_phone') or 
                         rec_data.get('requester_phone') or doc.get('phone'))
                email_hash = rec_data.get('email_hash') or doc.get('email_hash')
                name = (rec_data.get('name') or rec_data.get('full_name') or 
                        rec_data.get('display_name') or rec_data.get('requester_name') or 
                        doc.get('display_name') or doc.get('full_name') or doc.get('name'))

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
                    email=email,
                    phone=phone,
                    email_hash=email_hash,
                    name=name,
                    raw_details=rec_data
                ))

        # 2. customer_profiles / customer_profiles_primary / customer_profiles_failover_replica
        elif table in ('customer_profiles', 'customer_profiles_primary', 'customer_profiles_failover_replica'):
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='account_service',
                    resource_id=r_id,
                    data_category='USER_PROFILE',
                    state='PRESENT',
                    user_id=d.get('user_id'),
                    customer_reference=d.get('customer_reference'),
                    subject_reference=d.get('customer_reference') or d.get('user_id'),
                    email=d.get('email'),
                    phone=d.get('phone'),
                    email_hash=d.get('email_hash'),
                    name=d.get('full_name'),
                    raw_details=d
                ))

        # 3. search_documents / customer_search_documents / search_documents_primary
        elif table in ('customer_search_documents', 'search_documents_primary'):
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='search_service',
                    resource_id=r_id,
                    data_category='SEARCH_INDEX_ENTRY',
                    state='PRESENT',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('email'),
                    phone=d.get('phone'),
                    email_hash=d.get('email_hash'),
                    name=d.get('display_name'),
                    raw_details=d
                ))

        # 4. customer_analytics_profiles
        elif table == 'customer_analytics_profiles':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                has_id = any(d.get(k) for k in ('email', 'phone', 'email_hash', 'customer_reference'))
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='analytics_platform',
                    resource_id=r_id,
                    data_category='ANALYTICS_PROFILE',
                    state='PRESENT' if has_id else 'ANONYMIZED',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('email'),
                    phone=d.get('phone'),
                    email_hash=d.get('email_hash'),
                    raw_details=d
                ))

        # 5. support_records
        elif table == 'support_records':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                has_pii = any(d.get(k) for k in ('requester_email', 'requester_phone', 'requester_name'))
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='support_platform',
                    resource_id=r_id,
                    data_category='SUPPORT_MESSAGE',
                    state='PRESENT' if has_pii else 'REDACTED',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('requester_email'),
                    phone=d.get('requester_phone'),
                    name=d.get('requester_name'),
                    raw_details=d
                ))

        # 6. customer_exports
        elif table == 'customer_exports':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='export_service',
                    resource_id=r_id,
                    data_category='USER_EXPORT',
                    state='PRESENT',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('owner_email'),
                    phone=d.get('owner_phone'),
                    raw_details=d
                ))

        # 7. connector_subscriptions
        elif table == 'connector_subscriptions':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                is_active = d.get('enabled') in (1, True, '1', 'true', 'ACTIVE')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='integration_service',
                    resource_id=r_id,
                    data_category='DATA_FLOW',
                    state='ACTIVE' if is_active else 'DISABLED',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('customer_email'),
                    raw_details=d
                ))

        # 8. backup_restore_entries
        elif table == 'backup_restore_entries':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                is_allowed = d.get('restore_allowed') in (1, True, '1', 'true', 'ACTIVE')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='backup_service',
                    resource_id=r_id,
                    data_category='BACKUP_ARCHIVE',
                    state='ACTIVE' if is_allowed else 'BLOCKED',
                    customer_reference=d.get('customer_reference'),
                    email=d.get('customer_email'),
                    raw_details=d
                ))

        # 9. security_audit_records
        elif table == 'security_audit_records':
            cols = [col[1] for col in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                d = dict(zip(cols, row))
                r_id = d.get('resource_id')
                records.append(EvidenceRecord(
                    evidence_id=file_id,
                    file_path=file_path,
                    captured_at=captured_at,
                    origin=origin,
                    system_id='security_service',
                    resource_id=r_id,
                    data_category='SECURITY_AUDIT_LOG',
                    state='PRESENT',
                    subject_reference=d.get('subject_reference'),
                    raw_details=d
                ))

    db.close()
    return records
