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

            state = 'PRESENT'
            if status == 'NOT_FOUND':
                state = 'ABSENT'
            elif status == 'FOUND':
                state = 'PRESENT'
            elif status == 'IDENTIFIABLE':
                state = 'PRESENT'
            elif status == 'ANONYMIZED':
                state = 'ANONYMIZED'
            elif status == 'ACTIVE':
                state = 'ACTIVE'
            elif status == 'DISABLED':
                state = 'DISABLED'
            elif status == 'BLOCKED':
                state = 'BLOCKED'
            elif status == 'REDACTED':
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
