import os
import re
from typing import List
import pypdf
from src.models import EvidenceRecord

def parse_pdf_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for p in reader.pages:
            text += (p.extract_text() or "") + "\n"
    except Exception:
        return records

    # Extract resources
    resources = set(re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', text))
    emails = set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text))
    users = set(re.findall(r'\buser_\d+\b', text))

    # Match each resource or user found in document
    if resources:
        for r_id in resources:
            sys_id = origin or 'support_platform'
            data_cat = 'SUPPORT_ATTACHMENT'
            if r_id.startswith('support_'):
                sys_id = 'support_platform'
                data_cat = 'SUPPORT_ATTACHMENT'
            elif r_id.startswith('audit_record_'):
                sys_id = 'security_service'
                data_cat = 'SECURITY_AUDIT_LOG'
            elif r_id.startswith('account_'):
                sys_id = 'account_service'
                data_cat = 'USER_PROFILE'

            r_pos = text.lower().find(r_id.lower())
            best_email = None
            if emails:
                email_matches = [(m.start(), m.group().lower()) for m in re.finditer(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)]
                best_email = min(email_matches, key=lambda em: (0 if em[0] >= r_pos else 1, abs(em[0] - r_pos)))[1]

            best_user = None
            if users:
                user_matches = [(m.start(), m.group().lower()) for m in re.finditer(r'\buser_\d+\b', text, re.I)]
                best_user = min(user_matches, key=lambda um: (0 if um[0] >= r_pos else 1, abs(um[0] - r_pos)))[1]

            records.append(EvidenceRecord(
                evidence_id=file_id,
                file_path=file_path,
                captured_at=captured_at,
                origin=origin,
                system_id=sys_id,
                resource_id=r_id,
                data_category=data_cat,
                state='PRESENT',
                user_id=best_user,
                email=best_email,
                raw_details={'text_snippet': text[:500]}
            ))
    elif emails or users:
        # If no explicit resource_id like support_001, create record with document name as resource
        for u in users:
            records.append(EvidenceRecord(
                evidence_id=file_id,
                file_path=file_path,
                captured_at=captured_at,
                origin=origin,
                system_id='legal_retention_service' if 'legal' in file_path else 'account_service',
                resource_id=f"doc_{u}",
                data_category='LEGAL_HOLD_RECORD' if 'legal' in file_path else 'USER_PROFILE',
                state='PRESENT',
                user_id=u,
                raw_details={'text_snippet': text[:500]}
            ))
        for e in emails:
            records.append(EvidenceRecord(
                evidence_id=file_id,
                file_path=file_path,
                captured_at=captured_at,
                origin=origin,
                system_id='account_service',
                resource_id=f"doc_{e}",
                data_category='USER_PROFILE',
                state='PRESENT',
                email=e.lower(),
                raw_details={'text_snippet': text[:500]}
            ))

    return records
