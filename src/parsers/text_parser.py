import os
import re
from typing import List
from src.models import EvidenceRecord

def parse_text_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('- '):
                continue
            line = line[2:]
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 6:
                continue

            event_time, sys_id, r_id, cat, status, ident = parts[:6]

            status_clean = status.upper().strip()
            state = 'PRESENT'
            if status_clean in ('NOT_FOUND', 'ABSENT'):
                state = 'ABSENT'
            elif status_clean in ('FOUND', 'PRESENT', 'IDENTIFIABLE'):
                state = 'PRESENT'
            elif status_clean == 'ANONYMIZED':
                state = 'ANONYMIZED'
            elif status_clean in ('ACTIVE', 'ENABLED', 'REMAINS ENABLED'):
                state = 'ACTIVE'
            elif status_clean in ('DISABLED', 'STOPPED', 'BLOCKED_FLOW'):
                state = 'DISABLED'
            elif status_clean in ('BLOCKED', 'BLOCKED_RESTORE'):
                state = 'BLOCKED'
            elif status_clean == 'REDACTED':
                state = 'REDACTED'

            email = None
            user_id = None
            if '@' in ident:
                email = ident.lower()
            elif ident.startswith('user_'):
                user_id = ident

            records.append(EvidenceRecord(
                evidence_id=file_id,
                file_path=file_path,
                captured_at=captured_at,
                origin=origin,
                system_id=sys_id,
                resource_id=r_id,
                data_category=cat,
                state=state,
                user_id=user_id,
                customer_reference=ident if not email and not user_id and ident != 'no direct identifier' else None,
                subject_reference=ident if not email and not user_id and ident != 'no direct identifier' else None,
                email=email,
                raw_details={'status': status, 'identifier': ident}
            ))

    return records
